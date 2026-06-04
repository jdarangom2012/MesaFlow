import json
from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST

from accounts.permissions import ADMIN, CAJERO, COCINA, MESERO, SUPERADMIN, role_required, tenant_filter, user_can_access_module
from cash_register.services import get_open_session, record_order_payment
from kitchen.realtime import broadcast_order_created, broadcast_order_paid, broadcast_order_removed, broadcast_order_updated
from products.models import Product
from tables.models import RestaurantTable

from .models import Order, OrderItem


ACTIVE_ORDER_STATUSES = ['OPEN', 'PREPARING', 'READY']
ORDER_FILTERS = ['ALL', 'OPEN', 'PREPARING', 'READY', 'PAID', 'CANCELLED']


def sync_table_status(table):
    has_active_order = Order.objects.filter(
        restaurant=table.restaurant,
        table=table,
        status__in=ACTIVE_ORDER_STATUSES,
    ).exists()
    table.status = 'OCCUPIED' if has_active_order else 'FREE'
    table.save(update_fields=['status'])


@login_required
@role_required(SUPERADMIN, ADMIN, CAJERO, MESERO)
def orders_dashboard(request):
    selected_status = request.GET.get('status', 'ALL').upper()

    if selected_status not in ORDER_FILTERS:
        selected_status = 'ALL'

    orders = (
        Order.objects
        .filter(**tenant_filter(request))
        .select_related('restaurant', 'table')
        .prefetch_related('items__product')
        .order_by('-created_at')
    )

    if selected_status != 'ALL':
        orders = orders.filter(status=selected_status)

    status_counts = {
        status: Order.objects.filter(status=status, **tenant_filter(request)).count()
        for status, _label in Order.STATUS_CHOICES
    }
    status_counts['ALL'] = Order.objects.filter(**tenant_filter(request)).count()

    context = {
        'orders': orders,
        'restaurant': request.restaurant,
        'selected_status': selected_status,
        'status_filters': ORDER_FILTERS,
        'status_counts': status_counts,
    }

    return render(request, 'orders/index.html', context)


@login_required
@require_POST
@role_required(SUPERADMIN, ADMIN, CAJERO, MESERO)
def order_action(request, order_id):
    action = request.POST.get('action')
    selected_status = request.POST.get('status_filter', 'ALL')
    order = get_object_or_404(
        Order.objects.select_related('table', 'restaurant'),
        id=order_id,
        **tenant_filter(request),
    )

    with transaction.atomic():
        if action == 'mark_ready' and order.status in ['OPEN', 'PREPARING']:
            order.status = 'READY'
            order.save(update_fields=['status'])
            transaction.on_commit(lambda: broadcast_order_updated(order))

        elif action == 'mark_paid' and order.status == 'READY':
            if not get_open_session(order.restaurant):
                messages.warning(request, 'Debes abrir caja antes de registrar pagos')
                return redirect(f'{reverse("orders:list")}?status={selected_status}')

            order.status = 'PAID'
            order.payment_method = order.payment_method or 'CASH'
            order.paid_at = timezone.now()
            order.save(update_fields=['status', 'payment_method', 'paid_at'])
            sync_table_status(order.table)
            record_order_payment(order, request.user)
            transaction.on_commit(lambda: broadcast_order_paid(order))

        elif action == 'cancel' and order.status != 'PAID':
            order.status = 'CANCELLED'
            order.save(update_fields=['status'])
            sync_table_status(order.table)
            transaction.on_commit(lambda: broadcast_order_removed(order))

        elif action == 'reopen' and order.status == 'CANCELLED':
            order.status = 'OPEN'
            order.payment_method = ''
            order.paid_at = None
            order.save(update_fields=['status', 'payment_method', 'paid_at'])
            order.table.status = 'OCCUPIED'
            order.table.save(update_fields=['status'])
            order = (
                Order.objects
                .select_related('table')
                .prefetch_related('items__product')
                .get(id=order.id)
            )
            transaction.on_commit(lambda: broadcast_order_created(order))

    url = reverse('orders:list')

    if selected_status in ORDER_FILTERS:
        url = f'{url}?status={selected_status}'

    return redirect(url)


@require_POST
def create_order(request):
    try:
        payload = json.loads(request.body.decode('utf-8'))
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'JSON inválido'}, status=400)

    table_id = payload.get('table_id')
    items = payload.get('items', [])

    if not table_id:
        return JsonResponse({'success': False, 'error': 'Mesa requerida'}, status=400)

    if not isinstance(items, list) or not items:
        return JsonResponse({'success': False, 'error': 'Productos requeridos'}, status=400)

    try:
        table = RestaurantTable.objects.get(id=table_id)
    except RestaurantTable.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Mesa no encontrada'}, status=404)

    user = getattr(request, 'user', None)
    request_restaurant = getattr(request, 'restaurant', None)

    if user and user.is_authenticated:
        if not request_restaurant and not getattr(request, 'is_saas_superadmin', False):
            return JsonResponse({'success': False, 'error': 'Usuario sin restaurante asignado'}, status=403)

        if request_restaurant and table.restaurant_id != request_restaurant.id:
            return JsonResponse({'success': False, 'error': 'Mesa no pertenece a tu restaurante'}, status=403)

    active_order = Order.objects.filter(
        restaurant=table.restaurant,
        table=table,
        status__in=ACTIVE_ORDER_STATUSES,
    ).order_by('-created_at').first()

    if active_order:
        return JsonResponse({
            'success': False,
            'error': f'La mesa ya tiene la orden activa #{active_order.id}.',
            'order_id': active_order.id,
            'status': active_order.status,
        }, status=409)

    product_quantities = {}

    for item in items:
        product_id = item.get('product_id')
        quantity = item.get('quantity')

        if not product_id:
            return JsonResponse({'success': False, 'error': 'Producto requerido'}, status=400)

        try:
            product_id = int(product_id)
        except (TypeError, ValueError):
            return JsonResponse({'success': False, 'error': 'Producto inválido'}, status=400)

        try:
            quantity = int(quantity)
        except (TypeError, ValueError):
            return JsonResponse({'success': False, 'error': 'Cantidad inválida'}, status=400)

        if quantity <= 0:
            return JsonResponse({'success': False, 'error': 'La cantidad debe ser mayor a 0'}, status=400)

        product_quantities[product_id] = product_quantities.get(product_id, 0) + quantity

    products = Product.objects.filter(
        id__in=product_quantities.keys(),
        restaurant=table.restaurant,
        is_active=True,
        is_available=True,
        is_pos_available=True,
        category__is_active=True,
    )
    products_by_id = {product.id: product for product in products}

    if len(products_by_id) != len(product_quantities):
        return JsonResponse({'success': False, 'error': 'Uno o más productos no existen para esta mesa'}, status=404)

    subtotal = Decimal('0.00')
    order_items = []

    for product_id, quantity in product_quantities.items():
        product = products_by_id[product_id]
        item_subtotal = product.price * quantity
        subtotal += item_subtotal
        order_items.append({
            'product': product,
            'quantity': quantity,
            'unit_price': product.price,
            'subtotal': item_subtotal,
        })

    tax = (subtotal * Decimal('0.19')).quantize(Decimal('0.01'))
    total = subtotal + tax

    with transaction.atomic():
        if table.status != 'OCCUPIED':
            table.status = 'OCCUPIED'
            table.save(update_fields=['status'])

        order = Order.objects.create(
            restaurant=table.restaurant,
            table=table,
            status='OPEN',
            subtotal=subtotal,
            tax=tax,
            total=total,
        )

        OrderItem.objects.bulk_create([
            OrderItem(
                order=order,
                product=item['product'],
                quantity=item['quantity'],
                unit_price=item['unit_price'],
                subtotal=item['subtotal'],
            )
            for item in order_items
        ])

        order = (
            Order.objects
            .select_related('table')
            .prefetch_related('items__product')
            .get(id=order.id)
        )
        transaction.on_commit(lambda: broadcast_order_created(order))

    kitchen_print_url = reverse('orders:print_kitchen', args=[order.id])
    settings = get_restaurant_settings(order.restaurant)
    kitchen_width = getattr(settings, 'kitchen_ticket_width', '80') if settings else '80'
    if kitchen_width not in ['58', '80']:
        kitchen_width = '80'

    return JsonResponse({
        'success': True,
        'order_id': order.id,
        'subtotal': float(subtotal),
        'tax': float(tax),
        'total': float(total),
        'kitchen_print_url': f'{kitchen_print_url}?width={kitchen_width}&autoprint=1',
        'auto_print_kitchen': bool(settings and settings.enable_auto_print and settings.auto_print_kitchen),
    })


@login_required
@require_POST
@role_required(SUPERADMIN, ADMIN, CAJERO)
def pay_order(request, order_id):
    try:
        payload = json.loads(request.body.decode('utf-8') or '{}')
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'JSON inválido'}, status=400)

    payment_method = payload.get('payment_method')
    valid_methods = {method for method, _label in Order.PAYMENT_METHOD_CHOICES}

    if payment_method not in valid_methods:
        return JsonResponse({'success': False, 'error': 'Método de pago inválido'}, status=400)

    if not getattr(request, 'restaurant', None) and not getattr(request, 'is_saas_superadmin', False):
        return JsonResponse({'success': False, 'error': 'Usuario sin restaurante asignado'}, status=403)

    with transaction.atomic():
        order = get_object_or_404(
            Order.objects.select_related('table'),
            id=order_id,
            **tenant_filter(request),
        )

        if order.status != 'READY':
            return JsonResponse({'success': False, 'error': 'Solo se pueden cobrar órdenes listas'}, status=400)

        try:
            tip = max(Decimal(str(payload.get('tip', 0) or 0)), Decimal('0'))
            cash_received = max(Decimal(str(payload.get('cash_received', 0) or 0)), Decimal('0'))
        except InvalidOperation:
            return JsonResponse({'success': False, 'error': 'Revisa los valores ingresados para el pago'}, status=400)

        if payment_method == 'CASH' and cash_received < order.total + tip:
            return JsonResponse({'success': False, 'error': 'El efectivo recibido no cubre el total'}, status=400)

        if not get_open_session(order.restaurant):
            return JsonResponse({'success': False, 'error': 'Debes abrir caja antes de registrar pagos'}, status=400)

        order.status = 'PAID'
        order.payment_method = payment_method
        order.paid_at = timezone.now()
        order.save(update_fields=['status', 'payment_method', 'paid_at'])
        record_order_payment(order, request.user)

        table = order.table
        table.status = 'FREE'
        table.save(update_fields=['status'])

        transaction.on_commit(lambda: broadcast_order_paid(order))

    receipt_url = reverse('orders:print_receipt', args=[order.id])
    settings = get_restaurant_settings(order.restaurant)
    cashier_width = getattr(settings, 'cashier_ticket_width', '80') if settings else '80'
    if cashier_width not in ['58', '80']:
        cashier_width = '80'

    return JsonResponse({
        'success': True,
        'order_id': order.id,
        'status': order.status,
        'payment_method': order.payment_method,
        'paid_at': order.paid_at.isoformat() if order.paid_at else None,
        'subtotal': float(order.subtotal),
        'tax': float(order.tax),
        'total': float(order.total),
        'table_id': table.id,
        'table_status': table.status,
        'receipt_print_url': f'{receipt_url}?width={cashier_width}&autoprint=1',
        'auto_print_cashier': bool(settings and settings.enable_auto_print and settings.auto_print_cashier),
    })


@require_GET
def table_active_order(request, table_id):
    if not request.user.is_authenticated:
        return JsonResponse({
            'success': False,
            'error': 'Tu sesión expiró. Inicia sesión nuevamente.',
        }, status=401)

    if not user_can_access_module(request.user, 'pos'):
        return JsonResponse({
            'success': False,
            'error': 'Tu rol no tiene permiso para usar el POS.',
        }, status=403)

    if not getattr(request, 'restaurant', None) and not getattr(request, 'is_saas_superadmin', False):
        return JsonResponse({
            'success': False,
            'error': 'Usuario sin restaurante asignado.',
        }, status=403)

    table = RestaurantTable.objects.filter(
        id=table_id,
        **tenant_filter(request),
    ).first()

    if not table:
        return JsonResponse({
            'success': False,
            'error': 'Mesa no encontrada.',
        }, status=404)

    order = (
        Order.objects
        .filter(table=table, status__in=ACTIVE_ORDER_STATUSES, **tenant_filter(request))
        .order_by('-created_at')
        .first()
    )

    if not order:
        return JsonResponse({
            'success': True,
            'has_order': False,
            'table_id': table.id,
            'table_name': table.name,
            'table_capacity': table.capacity,
            'table_status': table.status,
        })

    return JsonResponse({
        'success': True,
        'has_order': True,
        'order_id': order.id,
        'status': order.status,
        'status_label': order.get_status_display(),
        'subtotal': float(order.subtotal),
        'tax': float(order.tax),
        'total': float(order.total),
        'table_id': table.id,
        'table_name': table.name,
        'table_capacity': table.capacity,
        'table_status': table.status,
        'created_at': order.created_at.isoformat(),
    })


@login_required
@role_required(SUPERADMIN, ADMIN, CAJERO, MESERO)
def ticket(request, order_id):
    return print_payment_ticket(request, order_id)


@login_required
@role_required(SUPERADMIN, ADMIN, COCINA)
def kitchen_ticket(request, order_id):
    return print_kitchen_ticket(request, order_id)


@login_required
@role_required(SUPERADMIN, ADMIN, CAJERO, COCINA, MESERO)
def print_kitchen_ticket(request, order_id):
    order = get_print_order(request, order_id)
    return render_print_ticket(request, order, 'print/kitchen_ticket.html')


@login_required
@role_required(SUPERADMIN, ADMIN, CAJERO, MESERO)
def print_payment_ticket(request, order_id):
    order = get_print_order(request, order_id)
    return render_print_ticket(request, order, 'print/payment_ticket.html')


@login_required
@role_required(SUPERADMIN, ADMIN, CAJERO, COCINA, MESERO)
def print_kitchen(request, order_id):
    return print_kitchen_ticket(request, order_id)


@login_required
@role_required(SUPERADMIN, ADMIN, CAJERO, MESERO)
def print_receipt(request, order_id):
    return print_payment_ticket(request, order_id)


def get_print_order(request, order_id):
    return get_object_or_404(
        Order.objects
        .select_related('restaurant', 'table')
        .prefetch_related('items__product'),
        id=order_id,
        **tenant_filter(request),
    )


def get_print_branding(order):
    try:
        settings = order.restaurant.settings
    except ObjectDoesNotExist:
        settings = None

    logo = ''

    if settings and settings.logo:
        logo = settings.logo.url

    return {
        'print_restaurant_name': order.restaurant.name,
        'print_logo': logo,
    }


def get_restaurant_settings(restaurant):
    try:
        return restaurant.settings
    except ObjectDoesNotExist:
        return None


def render_print_ticket(request, order, template_name):
    settings = get_restaurant_settings(order.restaurant)

    default_width = getattr(settings, 'cashier_ticket_width', '80') if template_name.endswith('payment_ticket.html') else getattr(settings, 'kitchen_ticket_width', '80')
    requested_width = request.GET.get('width') or default_width
    paper_width = '58' if requested_width == '58' else '80'

    try:
        tip = Decimal(request.GET.get('tip', '0') or '0')
    except (InvalidOperation, TypeError):
        tip = Decimal('0')

    if tip < 0:
        tip = Decimal('0')

    item_groups = {}
    for item in order.items.all():
        category = item.product.category.name if item.product and item.product.category else 'Productos'
        item_groups.setdefault(category, []).append(item)

    printer_name = ''
    if settings:
        printer_name = settings.cashier_printer_name if template_name.endswith('payment_ticket.html') else settings.kitchen_printer_name

    return render(request, template_name, {
        'order': order,
        'paper_width': paper_width,
        'printer_name': printer_name,
        'autoprint': request.GET.get('autoprint') == '1',
        'item_groups': item_groups.items(),
        'tip': tip,
        'total_with_tip': order.total + tip,
        **get_print_branding(order),
    })


def render_receipt(request, order, paper_width):
    try:
        tip = Decimal(request.GET.get('tip', '0') or '0')
    except (InvalidOperation, TypeError):
        tip = Decimal('0')

    if tip < 0:
        tip = Decimal('0')

    return render(request, 'orders/ticket.html', {
        'order': order,
        'paper_width': paper_width,
        'tip': tip,
        'total_with_tip': order.total + tip,
    })


def render_kitchen_ticket(request, order, paper_width):
    return render(request, 'orders/kitchen_ticket.html', {
        'order': order,
        'paper_width': paper_width,
    })
