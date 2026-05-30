from django.urls import path

from .views import (
    create_order,
    kitchen_ticket,
    order_action,
    orders_dashboard,
    pay_order,
    print_kitchen,
    print_kitchen_ticket,
    print_payment_ticket,
    print_receipt,
    table_active_order,
    ticket,
)

app_name = 'orders'

urlpatterns = [
    path('', orders_dashboard, name='list'),
    path('create/', create_order, name='create_order'),
    path('<int:order_id>/action/', order_action, name='action'),
    path('pay/<int:order_id>/', pay_order, name='pay_order'),
    path('table/<int:table_id>/active/', table_active_order, name='table_active_order'),
    path('ticket/<int:order_id>/', ticket, name='ticket'),
    path('kitchen-ticket/<int:order_id>/', kitchen_ticket, name='kitchen_ticket'),
    path('<int:order_id>/print-kitchen-ticket/', print_kitchen_ticket, name='print_kitchen_ticket'),
    path('<int:order_id>/print-payment-ticket/', print_payment_ticket, name='print_payment_ticket'),
    path('<int:order_id>/print-kitchen/', print_kitchen, name='print_kitchen'),
    path('<int:order_id>/print-receipt/', print_receipt, name='print_receipt'),
]
