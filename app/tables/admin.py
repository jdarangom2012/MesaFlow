from django.contrib import admin
from .models import RestaurantTable


@admin.register(RestaurantTable)
class RestaurantTableAdmin(admin.ModelAdmin):
    list_display = ('name', 'restaurant', 'capacity', 'status')
    list_filter = ('restaurant', 'status')
    search_fields = ('name', 'restaurant__name')
