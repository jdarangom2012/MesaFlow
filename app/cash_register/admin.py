from django.contrib import admin

from .models import CashMovement, CashRegisterSession


@admin.register(CashRegisterSession)
class CashRegisterSessionAdmin(admin.ModelAdmin):
    list_display = ('restaurant', 'status', 'opening_amount', 'expected_total', 'actual_total', 'difference', 'total_sales', 'total_tax', 'opened_by', 'opened_at', 'closed_at')
    list_filter = ('status', 'restaurant', 'opened_at')
    search_fields = ('restaurant__name', 'opened_by__username', 'closed_by__username')
    readonly_fields = ('opened_at', 'closed_at', 'difference')


@admin.register(CashMovement)
class CashMovementAdmin(admin.ModelAdmin):
    list_display = ('restaurant', 'session', 'movement_type', 'payment_method', 'amount', 'order', 'user', 'created_at')
    list_filter = ('movement_type', 'payment_method', 'restaurant', 'created_at')
    search_fields = ('restaurant__name', 'order__id', 'user__username', 'note')
    readonly_fields = ('created_at',)
