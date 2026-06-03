from datetime import datetime, timedelta

from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Count, DecimalField, Prefetch, Q, Sum, Value
from django.db.models.functions import Coalesce, ExtractHour, TruncDate
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from accounts.permissions import ADMIN, CAJERO, MESERO, SUPERADMIN, role_required, tenant_filter
from cash_register.models import CashRegisterSession
from orders.models import Order, OrderItem
from products.models import ProductCategory, Product
from tables.models import RestaurantTable

def home(request):
    return render(request, 'home.html')


def _dashboard_payload(request):
    restaurant = request.restaurant
    today = timezone.localdate()
    today_start = timezone.make_aware(datetime.combine(today, datetime.min.time()))
    week_start = today_start - timedelta(days=today.weekday())
    month_start = timezone.make_aware(datetime.combine(today.replace(day=1), datetime.min.time()))
    seven_days_start = today_start - timedelta(days=6)
    now = timezone.now()
    orders = Order.objects.filter(**tenant_filter(request))
    paid_orders_today = orders.filter(status='PAID', paid_at__gte=today_start, paid_at__lte=now)
    zero_money = Value(0, output_field=DecimalField(max_digits=12, decimal_places=2))

    order_metrics = orders.aggregate(
        sales_today=Coalesce(Sum('total', filter=Q(status='PAID', paid_at__gte=today_start, paid_at__lte=now)), zero_money),
        sales_week=Coalesce(Sum('total', filter=Q(status='PAID', paid_at__gte=week_start, paid_at__lte=now)), zero_money),
        sales_month=Coalesce(Sum('total', filter=Q(status='PAID', paid_at__gte=month_start, paid_at__lte=now)), zero_money),
        orders_today=Count('id', filter=Q(created_at__date=today)),
        paid_orders=Count('id', filter=Q(status='PAID')),
        open_orders=Count('id', filter=Q(status='OPEN')),
        preparing_orders=Count('id', filter=Q(status='PREPARING')),
        ready_orders=Count('id', filter=Q(status='READY')),
        average_ticket=Coalesce(Avg('total', filter=Q(status='PAID', paid_at__gte=today_start, paid_at__lte=now)), zero_money),
    )
    table_metrics = RestaurantTable.objects.filter(**tenant_filter(request)).aggregate(
        free_tables=Count('id', filter=Q(status='FREE')),
        occupied_tables=Count('id', filter=Q(status='OCCUPIED')),
    )

    top_products = list(
        OrderItem.objects
        .filter(order__in=paid_orders_today)
        .values('product__name')
        .annotate(quantity_sold=Coalesce(Sum('quantity'), Value(0)), revenue=Coalesce(Sum('subtotal'), zero_money))
        .order_by('-quantity_sold', '-revenue')[:6]
    )
    top_categories = list(
        OrderItem.objects
        .filter(order__in=paid_orders_today)
        .values('product__category__name')
        .annotate(quantity_sold=Coalesce(Sum('quantity'), Value(0)), revenue=Coalesce(Sum('subtotal'), zero_money))
        .order_by('-revenue', '-quantity_sold')[:6]
    )
    tables_usage = list(
        paid_orders_today
        .values('table__name')
        .annotate(orders=Count('id'), revenue=Coalesce(Sum('total'), zero_money))
        .order_by('-orders', '-revenue')[:6]
    )
    payment_methods = list(
        paid_orders_today
        .values('payment_method')
        .annotate(total=Coalesce(Sum('total'), zero_money))
        .order_by('-total')
    )

    recent_orders = list(
        orders
        .select_related('table')
        .prefetch_related('items__product')
        .order_by('-created_at')[:8]
    )

    sales_by_hour = (
        paid_orders_today
        .annotate(hour=ExtractHour('paid_at'))
        .values('hour')
        .annotate(total=Coalesce(Sum('total'), zero_money), orders=Count('id'))
        .order_by('hour')
    )
    hour_totals = {row['hour']: float(row['total']) for row in sales_by_hour if row['hour'] is not None}
    hour_labels = [f'{hour:02d}:00' for hour in range(24)]
    hour_values = [hour_totals.get(hour, 0) for hour in range(24)]
    sales_by_day = (
        orders
        .filter(status='PAID', paid_at__gte=seven_days_start, paid_at__lte=now)
        .annotate(day=TruncDate('paid_at'))
        .values('day')
        .annotate(total=Coalesce(Sum('total'), zero_money))
        .order_by('day')
    )
    day_totals = {row['day']: float(row['total']) for row in sales_by_day if row['day'] is not None}
    day_dates = [today - timedelta(days=offset) for offset in range(6, -1, -1)]

    status_labels = ['OPEN', 'PREPARING', 'READY', 'PAID']
    status_values = [
        order_metrics['open_orders'],
        order_metrics['preparing_orders'],
        order_metrics['ready_orders'],
        order_metrics['paid_orders'],
    ]

    peak_hours_raw = (
        orders
        .filter(created_at__gte=today_start, created_at__lte=now)
        .annotate(hour=ExtractHour('created_at'))
        .values('hour')
        .annotate(orders=Count('id'))
        .order_by('-orders', 'hour')[:4]
    )
    peak_hours = [
        {
            'label': f'{row["hour"]:02d}:00 - {(row["hour"] + 1) % 24:02d}:00',
            'orders': row['orders'],
        }
        for row in peak_hours_raw
        if row['hour'] is not None
    ]

    activity = []
    for order in recent_orders:
        activity.append({
            'order_id': order.id,
            'table': order.table.name,
            'status': order.status,
            'status_label': order.get_status_display(),
            'total': float(order.total),
            'time': order.created_at.strftime('%H:%M'),
        })

    active_orders = list(
        orders
        .filter(status__in=['OPEN', 'PREPARING', 'READY'])
        .select_related('table')
        .order_by('created_at')
    )
    delayed_orders = [
        order for order in active_orders
        if (now - order.created_at).total_seconds() >= 15 * 60
    ]
    long_occupied_tables = [
        order for order in active_orders
        if (now - order.created_at).total_seconds() >= 60 * 60
    ]
    completed_today = orders.filter(status='PAID', paid_at__gte=today_start, paid_at__lte=now)
    kitchen_durations = [
        max((order.paid_at - order.created_at).total_seconds() / 60, 0)
        for order in completed_today
        if order.paid_at
    ]
    average_kitchen_time = round(sum(kitchen_durations) / len(kitchen_durations)) if kitchen_durations else 0
    open_cash_count = CashRegisterSession.objects.filter(
        status=CashRegisterSession.STATUS_OPEN,
        **tenant_filter(request),
    ).count()
    alerts = []
    if delayed_orders:
        alerts.append({'level': 'warning', 'title': 'Órdenes demoradas', 'copy': f'{len(delayed_orders)} órdenes activas superan 15 minutos.'})
    if long_occupied_tables:
        alerts.append({'level': 'critical', 'title': 'Mesas ocupadas por mucho tiempo', 'copy': f'{len(long_occupied_tables)} mesas superan 60 minutos de operación.'})
    if average_kitchen_time > 20:
        alerts.append({'level': 'critical', 'title': 'Cocina lenta', 'copy': f'El tiempo promedio de cocina está en {average_kitchen_time} min.'})
    if open_cash_count:
        alerts.append({'level': 'info', 'title': 'Caja abierta', 'copy': f'{open_cash_count} caja(s) operativa(s) en este momento.'})

    chart_data = {
        'salesByHour': {
            'labels': hour_labels,
            'values': hour_values,
        },
        'orderStatus': {
            'labels': status_labels,
            'values': status_values,
        },
        'salesByDay': {
            'labels': [day.strftime('%d %b') for day in day_dates],
            'values': [day_totals.get(day, 0) for day in day_dates],
        },
        'paymentMethods': {
            'labels': [dict(Order.PAYMENT_METHOD_CHOICES).get(row['payment_method'], 'Sin método') for row in payment_methods],
            'values': [float(row['total']) for row in payment_methods],
        },
        'topProducts': {
            'labels': [row['product__name'] for row in top_products],
            'values': [int(row['quantity_sold']) for row in top_products],
        },
        'topCategories': {
            'labels': [row['product__category__name'] for row in top_categories],
            'values': [float(row['revenue']) for row in top_categories],
        },
    }

    return {
        'restaurant': restaurant,
        'sales_today': order_metrics['sales_today'],
        'sales_week': order_metrics['sales_week'],
        'sales_month': order_metrics['sales_month'],
        'orders_today': order_metrics['orders_today'],
        'paid_orders': order_metrics['paid_orders'],
        'open_orders': order_metrics['open_orders'],
        'preparing_orders': order_metrics['preparing_orders'],
        'ready_orders': order_metrics['ready_orders'],
        'average_ticket': order_metrics['average_ticket'],
        'free_tables': table_metrics['free_tables'],
        'occupied_tables': table_metrics['occupied_tables'],
        'active_orders': len(active_orders),
        'average_kitchen_time': average_kitchen_time,
        'cash_register_open': open_cash_count > 0,
        'cash_register_label': 'Abierta' if open_cash_count else 'Cerrada',
        'top_product': top_products[0]['product__name'] if top_products else 'Sin datos',
        'top_category': top_categories[0]['product__category__name'] if top_categories else 'Sin datos',
        'top_table': tables_usage[0]['table__name'] if tables_usage else 'Sin datos',
        'top_products': top_products,
        'top_categories': top_categories,
        'alerts': alerts,
        'recent_orders': recent_orders,
        'activity': activity,
        'peak_hours': peak_hours,
        'chart_data': chart_data,
        'today': today,
    }


@login_required
@role_required(SUPERADMIN, ADMIN)
def dashboard(request):
    return render(request, 'dashboard/index.html', _dashboard_payload(request))


@login_required
@role_required(SUPERADMIN, ADMIN)
def dashboard_data(request):
    payload = _dashboard_payload(request)

    return JsonResponse({
        'kpis': {
            'sales_today': float(payload['sales_today']),
            'sales_week': float(payload['sales_week']),
            'sales_month': float(payload['sales_month']),
            'orders_today': payload['orders_today'],
            'paid_orders': payload['paid_orders'],
            'open_orders': payload['open_orders'],
            'preparing_orders': payload['preparing_orders'],
            'ready_orders': payload['ready_orders'],
            'average_ticket': float(payload['average_ticket']),
            'free_tables': payload['free_tables'],
            'occupied_tables': payload['occupied_tables'],
            'active_orders': payload['active_orders'],
            'average_kitchen_time': payload['average_kitchen_time'],
            'cash_register_open': payload['cash_register_open'],
            'cash_register_label': payload['cash_register_label'],
            'top_product': payload['top_product'],
            'top_category': payload['top_category'],
            'top_table': payload['top_table'],
        },
        'top_products': [
            {
                'name': row['product__name'],
                'quantity_sold': int(row['quantity_sold']),
                'revenue': float(row['revenue']),
            }
            for row in payload['top_products']
        ],
        'activity': payload['activity'],
        'alerts': payload['alerts'],
        'peak_hours': payload['peak_hours'],
        'chart_data': payload['chart_data'],
    })



@login_required
@role_required(SUPERADMIN, ADMIN, CAJERO, MESERO)
def pos(request):

    products = (
        Product.objects
        .filter(
            restaurant=request.restaurant,
            is_active=True,
            is_pos_available=True,
            is_available=True,
            category__is_active=True,
        )
        .select_related('category')
        .order_by('category__sort_order', 'category__name', 'sort_order', 'name')
    )

    categories = (
        ProductCategory.objects
        .filter(is_active=True, restaurant=request.restaurant)
        .prefetch_related(Prefetch('products', queryset=products, to_attr='pos_products'))
        .order_by('sort_order', 'name')
    )

    tables = list(RestaurantTable.objects.filter(restaurant=request.restaurant, is_active=True).order_by('sort_order', 'name'))
    active_orders = (
        Order.objects
        .filter(restaurant=request.restaurant, status__in=['OPEN', 'PREPARING', 'READY'])
        .select_related('table')
        .order_by('-created_at')
    )
    active_orders_by_table = {order.table_id: order for order in active_orders}

    for table in tables:
        table.active_order = active_orders_by_table.get(table.id)

    context = {
        'categories': categories,
        'products': products,
        'tables': tables,
    }

    return render(request, 'pos/index.html', context)


def qr_menu(request, table_id):
    table = get_object_or_404(RestaurantTable, id=table_id)
    categories = (
        ProductCategory.objects
        .filter(is_active=True, restaurant=table.restaurant)
        .prefetch_related('products')
        .order_by('name')
    )
    products = (
        Product.objects
        .filter(is_active=True, is_available=True, restaurant=table.restaurant)
        .select_related('category')
        .order_by('category__name', 'name')
    )

    context = {
        'table': table,
        'categories': categories,
        'products': products,
    }

    return render(request, 'menu/index.html', context)
