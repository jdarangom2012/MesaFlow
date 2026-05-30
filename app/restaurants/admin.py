from django.contrib import admin

from .models import Restaurant, RestaurantSettings


class RestaurantSettingsInline(admin.StackedInline):
    model = RestaurantSettings
    extra = 0
    max_num = 1
    can_delete = False
    fieldsets = (
        ('Branding', {
            'fields': ('logo', 'primary_color', 'secondary_color'),
        }),
        ('Operación', {
            'fields': ('iva_percentage', 'tip_percentage', 'currency', 'enable_qr_orders', 'enable_tips'),
        }),
        ('Contacto', {
            'fields': ('whatsapp_number', 'address'),
        }),
        ('Impresión', {
            'fields': (
                'enable_auto_print',
                'auto_print_kitchen',
                'auto_print_cashier',
                'kitchen_ticket_width',
                'cashier_ticket_width',
                'kitchen_printer_name',
                'cashier_printer_name',
            ),
        }),
    )

@admin.register(Restaurant)
class RestaurantAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'company', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'slug', 'company__name')
    prepopulated_fields = {'slug': ('name',)}
    inlines = (RestaurantSettingsInline,)


@admin.register(RestaurantSettings)
class RestaurantSettingsAdmin(admin.ModelAdmin):
    list_display = ('restaurant', 'currency', 'iva_percentage', 'tip_percentage', 'enable_auto_print', 'kitchen_ticket_width', 'cashier_ticket_width')
    list_filter = ('currency', 'enable_qr_orders', 'enable_tips', 'enable_auto_print', 'kitchen_ticket_width', 'cashier_ticket_width')
    search_fields = ('restaurant__name', 'whatsapp_number', 'kitchen_printer_name', 'cashier_printer_name')
