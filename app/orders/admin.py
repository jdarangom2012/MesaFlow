from django.contrib import admin

from .models import Order, OrderItem

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'table', 'status', 'payment_method', 'subtotal', 'tax', 'total', 'paid_at', 'created_at')
    list_filter = ('status', 'payment_method', 'paid_at', 'created_at')
    search_fields = ('id', 'table__name')


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'order', 'product', 'quantity', 'unit_price', 'subtotal')
    search_fields = ('order__id', 'product__name')
