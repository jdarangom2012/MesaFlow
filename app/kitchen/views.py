from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Case, IntegerField, Value, When
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_GET, require_http_methods

from accounts.permissions import ADMIN, COCINA, SUPERADMIN, role_required, tenant_filter
from cash_register.services import record_order_payment
from kitchen.realtime import broadcast_order_paid, broadcast_order_updated
from orders.models import Order


KITCHEN_ACTIVE_STATUSES = ['OPEN', 'PREPARING', 'READY']


def _sync_table_status(table):
    has_active_order = Order.objects.filter(
        restaurant=table.restaurant,
        table=table,
        status__in=KITCHEN_ACTIVE_STATUSES,
    ).exists()
    table.status = 'OCCUPIED' if has_active_order else 'FREE'
    table.save(update_fields=['status'])


def _decorate_order(order):
    elapsed = timezone.now() - order.created_at
    elapsed_minutes = max(int(elapsed.total_seconds() // 60), 0)

    order.elapsed_minutes = elapsed_minutes
    order.elapsed_label = f'{elapsed_minutes} min'
    order.elapsed_level = 'critical' if elapsed_minutes >= 25 else 'warning' if elapsed_minutes >= 15 else 'normal'
    order.server_label = 'Equipo'

    return order


def _get_kitchen_orders(request):
    orders = (
        Order.objects
        .filter(status__in=KITCHEN_ACTIVE_STATUSES, **tenant_filter(request))
        .select_related('table')
        .prefetch_related('items__product')
        .annotate(
            kitchen_priority=Case(
                When(status='OPEN', then=Value(0)),
                When(status='PREPARING', then=Value(1)),
                When(status='READY', then=Value(2)),
                default=Value(3),
                output_field=IntegerField(),
            )
        )
        .order_by('kitchen_priority', 'created_at')
    )

    return [_decorate_order(order) for order in orders]


def _build_kitchen_context(request):
    orders = _get_kitchen_orders(request)
    status_counts = {
        status: Order.objects.filter(status=status, **tenant_filter(request)).count()
        for status in KITCHEN_ACTIVE_STATUSES
    }
    elapsed_minutes = [order.elapsed_minutes for order in orders]
    average_elapsed = round(sum(elapsed_minutes) / len(elapsed_minutes)) if elapsed_minutes else 0

    return {
        'orders': orders,
        'restaurant': request.restaurant,
        'status_counts': status_counts,
        'average_elapsed': average_elapsed,
    }


@require_http_methods(['GET', 'POST'])
@login_required
@role_required(SUPERADMIN, ADMIN, COCINA)
def kitchen_display(request):
    if request.method == 'POST':
        order = get_object_or_404(
            Order.objects.select_related('table', 'restaurant'),
            id=request.POST.get('order_id'),
            **tenant_filter(request),
        )
        next_status = request.POST.get('status')
        valid_transition = False

        with transaction.atomic():
            if order.status == 'OPEN' and next_status == 'PREPARING':
                order.status = next_status
                order.save(update_fields=['status'])
                transaction.on_commit(lambda: broadcast_order_updated(order))
                valid_transition = True

            elif order.status == 'PREPARING' and next_status == 'READY':
                order.status = next_status
                order.save(update_fields=['status'])
                transaction.on_commit(lambda: broadcast_order_updated(order))
                valid_transition = True

            elif order.status == 'READY' and next_status == 'PAID':
                order.status = 'PAID'
                order.payment_method = order.payment_method or 'CASH'
                order.paid_at = timezone.now()
                order.save(update_fields=['status', 'payment_method', 'paid_at'])
                _sync_table_status(order.table)
                record_order_payment(order, request.user)
                transaction.on_commit(lambda: broadcast_order_paid(order))
                valid_transition = True

        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            if not valid_transition:
                return JsonResponse({
                    'success': False,
                    'error': 'Transición no permitida para esta orden.',
                }, status=400)

            return JsonResponse({
                'success': True,
                'order_id': order.id,
                'status': order.status,
                'status_label': order.get_status_display(),
            })

        return redirect('kitchen')

    return render(request, 'kitchen/index.html', _build_kitchen_context(request))


@require_GET
@login_required
@role_required(SUPERADMIN, ADMIN, COCINA)
def kitchen_orders_partial(request):
    return render(request, 'kitchen/_orders.html', _build_kitchen_context(request))
