from django.contrib import admin

from .models import UserRestaurant


@admin.register(UserRestaurant)
class UserRestaurantAdmin(admin.ModelAdmin):
    list_display = ('user', 'restaurant', 'role')
    search_fields = ('user__username', 'user__email', 'restaurant__name')
    list_filter = ('restaurant', 'role')
