from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from decimal import Decimal, InvalidOperation
from django.db import transaction
from django.db.models import Avg, Count, DecimalField, Sum, Value
from django.db.models.functions import Coalesce
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from accounts.permissions import ADMIN, CAJERO, SUPERADMIN, role_required, tenant_filter
from cash_register.services import get_open_session, record_order_payment
from kitchen.realtime import broadcast_order_paid
from orders.models import Order
from orders.views import sync_table_status


PAYMENT_STATUS_FILTERS = ['READY', 'OPEN', 'PAID']


@login_required
@role_required(SUPERADMIN, ADMIN, CAJERO)
def payments_dashboard(request):
    selected_status = request.GET.get('status', 'READY').upper()

    if selected_status not in PAYMENT_STATUS_FILTERS:
        selected_status = 'READY'

    ready_orders = Order.objects.filter(
        status='READY',
        **tenant_filter(request),
    )
    today = timezone.localdate()
    paid_today = Order.objects.filter(
        status='PAID',
        paid_at__date=today,
        **tenant_filter(request),
    )
    zero_money = Value(0, output_field=DecimalField(max_digits=12, decimal_places=2))

    pending_metrics = ready_orders.aggregate(
        payments_pending=Count('id'),
        total_pending=Coalesce(Sum('total'), zero_money),
    )
    paid_metrics = paid_today.aggregate(
        paid_today=Count('id'),
        average_ticket=Coalesce(Avg('total'), zero_money),
    )

    orders = (
        Order.objects
        .filter(status=selected_status, **tenant_filter(request))
        .select_related('restaurant', 'table')
        .prefetch_related('items__product')
        .order_by('created_at')
    )

    context = {
        'orders': orders,
        'restaurant': request.restaurant,
        'selected_status': selected_status,
        'status_filters': PAYMENT_STATUS_FILTERS,
        'payments_pending': pending_metrics['payments_pending'],
        'total_pending': pending_metrics['total_pending'],
        'paid_today': paid_metrics['paid_today'],
        'average_ticket': paid_metrics['average_ticket'],
        'payment_methods': Order.PAYMENT_METHOD_CHOICES,
        'auto_print_receipt_url': request.session.pop('auto_print_receipt_url', ''),
    }

    return render(request, 'payments/index.html', context)


@login_required
@require_POST
@role_required(SUPERADMIN, ADMIN, CAJERO)
def confirm_payment(request, order_id):
    payment_method = request.POST.get('payment_method', '').upper()
    valid_methods = {method for method, _label in Order.PAYMENT_METHOD_CHOICES}

    if payment_method not in valid_methods:
        messages.error(request, 'Selecciona un método de pago válido.')
        return redirect('payments:dashboard')

    with transaction.atomic():
        order = get_object_or_404(
            Order.objects.select_related('table', 'restaurant'),
            id=order_id,
            **tenant_filter(request),
        )

        if order.status != 'READY':
            messages.error(request, 'Solo se pueden cobrar órdenes en estado READY.')
            return redirect('payments:dashboard')

        try:
            tip = max(Decimal(request.POST.get('tip', '0') or '0'), Decimal('0'))
            cash_received = max(Decimal(request.POST.get('cash_received', '0') or '0'), Decimal('0'))
        except InvalidOperation:
            messages.error(request, 'Revisa los valores ingresados para el pago.')
            return redirect('payments:dashboard')

        if payment_method == 'CASH' and cash_received < order.total + tip:
            messages.warning(request, 'El efectivo recibido no cubre el total')
            return redirect('payments:dashboard')

        if not get_open_session(order.restaurant):
            messages.warning(request, 'Debes abrir caja antes de registrar pagos')
            return redirect('payments:dashboard')

        order.status = 'PAID'
        order.payment_method = payment_method
        order.paid_at = timezone.now()
        order.save(update_fields=['status', 'payment_method', 'paid_at'])
        sync_table_status(order.table)
        record_order_payment(order, request.user)

        transaction.on_commit(lambda: broadcast_order_paid(order))

    try:
        settings = order.restaurant.settings
    except ObjectDoesNotExist:
        settings = None

    if settings and settings.enable_auto_print and settings.auto_print_cashier:
        width = settings.cashier_ticket_width if settings.cashier_ticket_width in ['58', '80'] else '80'
        request.session['auto_print_receipt_url'] = f'{reverse("orders:print_payment_ticket", args=[order.id])}?width={width}&autoprint=1'

    messages.success(request, f'Orden #{order.id} cobrada correctamente.')
    return redirect('payments:dashboard')
