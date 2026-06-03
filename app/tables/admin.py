from django.contrib import admin
from .models import RestaurantTable


@admin.register(RestaurantTable)
class RestaurantTableAdmin(admin.ModelAdmin):
    list_display = ('name', 'restaurant', 'capacity', 'type', 'status', 'is_active', 'sort_order')
    list_filter = ('restaurant', 'type', 'status', 'is_active')
    search_fields = ('name', 'restaurant__name')
    ordering = ('restaurant__name', 'sort_order', 'name')
