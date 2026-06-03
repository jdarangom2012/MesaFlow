from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from accounts.permissions import ADMIN, MESERO, SUPERADMIN, role_required, tenant_filter, user_has_role
from orders.models import Order

from .forms import RestaurantTableForm
from .models import RestaurantTable


ACTIVE_ORDER_STATUSES = ['OPEN', 'PREPARING', 'READY']


@login_required
@role_required(SUPERADMIN, ADMIN, MESERO)
def tables_dashboard(request):
    can_manage_tables = user_has_role(request.user, {SUPERADMIN, ADMIN})
    superadmin_global = user_has_role(request.user, SUPERADMIN) and not getattr(request, 'restaurant', None)

    if not getattr(request, 'restaurant', None) and not superadmin_global:
        return render(request, 'auth/403.html', {
            'message': 'Selecciona o asigna un restaurante para administrar mesas.',
        }, status=403)

    tables_queryset = (
        RestaurantTable.objects
        .filter(**tenant_filter(request))
        .prefetch_related('orders')
        .order_by('sort_order', 'name')
    )

    if not can_manage_tables:
        tables_queryset = tables_queryset.filter(is_active=True)

    tables = list(tables_queryset)
    active_orders = (
        Order.objects
        .filter(status__in=ACTIVE_ORDER_STATUSES, **tenant_filter(request))
        .select_related('table')
        .order_by('-created_at')
    )
    active_orders_by_table = {order.table_id: order for order in active_orders}

    table_cards = []
    visual_counts = {
        'free': 0,
        'occupied': 0,
        'preparing': 0,
        'ready': 0,
        'paid': 0,
    }

    for table in tables:
        active_order = active_orders_by_table.get(table.id)
        visual_status = 'free'
        visual_label = 'Libre'

        if not table.is_active:
            visual_status = 'inactive'
            visual_label = 'Inactiva'
        elif active_order:
            if active_order.status == 'OPEN':
                visual_status = 'occupied'
                visual_label = 'Ocupada'
            elif active_order.status == 'PREPARING':
                visual_status = 'preparing'
                visual_label = 'Preparando'
            elif active_order.status == 'READY':
                visual_status = 'ready'
                visual_label = 'Lista cobro'
        elif table.status == 'RESERVED':
            visual_status = 'reserved'
            visual_label = 'Reservada'
        elif table.status == 'PAYMENT_PENDING':
            visual_status = 'ready'
            visual_label = 'Lista cobro'

        if table.is_active:
            visual_counts[visual_status if visual_status in visual_counts else 'occupied'] = visual_counts.get(visual_status, 0) + 1

        table.edit_form = RestaurantTableForm(instance=table, include_restaurant=superadmin_global)
        table_cards.append({
            'table': table,
            'active_order': active_order,
            'visual_status': visual_status,
            'visual_label': visual_label,
        })

    status_counts = {
        status: RestaurantTable.objects.filter(
            status=status,
            is_active=True,
            **tenant_filter(request),
        ).count()
        for status, _label in RestaurantTable.STATUS_CHOICES
    }

    context = {
        'table_cards': table_cards,
        'status_counts': status_counts,
        'visual_counts': visual_counts,
        'restaurant': request.restaurant,
        'create_form': RestaurantTableForm(include_restaurant=superadmin_global),
        'can_manage_tables': can_manage_tables,
        'superadmin_global': superadmin_global,
        'table_types': RestaurantTable.TYPE_CHOICES,
    }

    return render(request, 'tables/index.html', context)


@login_required
@require_POST
@role_required(SUPERADMIN, ADMIN)
def table_create(request):
    superadmin_global = user_has_role(request.user, SUPERADMIN) and not getattr(request, 'restaurant', None)

    if not getattr(request, 'restaurant', None) and not superadmin_global:
        messages.error(request, 'No hay restaurante activo para crear mesas.')
        return redirect('tables_dashboard')

    form = RestaurantTableForm(request.POST, include_restaurant=superadmin_global)

    if form.is_valid():
        table = form.save(commit=False)
        table.restaurant = form.cleaned_data['restaurant'] if superadmin_global else request.restaurant
        table.status = 'FREE'
        table.save()
        messages.success(request, f'Mesa {table.name} creada correctamente.')
    else:
        messages.error(request, 'Revisa los campos de la mesa.')

    return redirect('tables_dashboard')


@login_required
@require_POST
@role_required(SUPERADMIN, ADMIN)
def table_edit(request, table_id):
    superadmin_global = user_has_role(request.user, SUPERADMIN) and not getattr(request, 'restaurant', None)
    table = get_object_or_404(RestaurantTable, id=table_id, **tenant_filter(request))
    form = RestaurantTableForm(request.POST, instance=table, include_restaurant=superadmin_global)

    if form.is_valid():
        table = form.save(commit=False)
        if superadmin_global:
            table.restaurant = form.cleaned_data['restaurant']
        table.save()
        messages.success(request, f'Mesa {table.name} actualizada.')
    else:
        messages.error(request, 'No se pudo actualizar la mesa. Revisa los campos.')

    return redirect('tables_dashboard')


@login_required
@require_POST
@role_required(SUPERADMIN, ADMIN)
def table_delete(request, table_id):
    table = get_object_or_404(RestaurantTable, id=table_id, **tenant_filter(request))
    table.is_active = False
    table.save(update_fields=['is_active'])
    messages.success(request, f'Mesa {table.name} desactivada.')

    return redirect('tables_dashboard')


@login_required
@require_POST
@role_required(SUPERADMIN, ADMIN, MESERO)
def close_table(request, table_id):
    table = get_object_or_404(
        RestaurantTable,
        id=table_id,
        **tenant_filter(request),
    )

    has_active_order = Order.objects.filter(
        table=table,
        status__in=ACTIVE_ORDER_STATUSES,
        **tenant_filter(request),
    ).exists()
    table.status = 'OCCUPIED' if has_active_order else 'FREE'
    table.save(update_fields=['status'])

    return redirect('tables_dashboard')


@login_required
@require_POST
@role_required(SUPERADMIN, ADMIN, MESERO)
def release_table(request, table_id):
    table = get_object_or_404(
        RestaurantTable,
        id=table_id,
        **tenant_filter(request),
    )

    with transaction.atomic():
        Order.objects.filter(
            table=table,
            status__in=ACTIVE_ORDER_STATUSES,
            **tenant_filter(request),
        ).update(status='PAID', paid_at=timezone.now())

        table.status = 'FREE'
        table.save(update_fields=['status'])

    return redirect('tables_dashboard')
