from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from accounts.permissions import ADMIN, MESERO, SUPERADMIN, role_required, tenant_filter
from orders.models import Order

from .models import RestaurantTable


ACTIVE_ORDER_STATUSES = ['OPEN', 'PREPARING', 'READY']


@login_required
@role_required(SUPERADMIN, ADMIN, MESERO)
def tables_dashboard(request):
    tables = (
        RestaurantTable.objects
        .filter(**tenant_filter(request))
        .prefetch_related('orders')
        .order_by('name')
    )

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

        if active_order:
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

        visual_counts[visual_status if visual_status in visual_counts else 'occupied'] = visual_counts.get(visual_status, 0) + 1
        table_cards.append({
            'table': table,
            'active_order': active_order,
            'visual_status': visual_status,
            'visual_label': visual_label,
        })

    status_counts = {
        status: RestaurantTable.objects.filter(
            status=status,
            **tenant_filter(request),
        ).count()
        for status, _label in RestaurantTable.STATUS_CHOICES
    }

    context = {
        'table_cards': table_cards,
        'status_counts': status_counts,
        'visual_counts': visual_counts,
        'restaurant': request.restaurant,
    }

    return render(request, 'tables/index.html', context)


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
