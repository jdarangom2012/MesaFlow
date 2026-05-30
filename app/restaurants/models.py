from django.db import models
from companies.models import Company

class Restaurant(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='restaurants')
    name = models.CharField(max_length=150)
    slug = models.SlugField(max_length=160, unique=True)
    logo = models.ImageField(upload_to='restaurants/logos/', blank=True, null=True)
    primary_color = models.CharField(max_length=20, default='#00D4FF')
    address = models.CharField(max_length=250, blank=True, null=True)
    phone = models.CharField(max_length=30, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class RestaurantSettings(models.Model):
    TICKET_WIDTH_58 = '58'
    TICKET_WIDTH_80 = '80'

    TICKET_WIDTH_CHOICES = [
        (TICKET_WIDTH_58, '58mm'),
        (TICKET_WIDTH_80, '80mm'),
    ]

    restaurant = models.OneToOneField(Restaurant, on_delete=models.CASCADE, related_name='settings')
    logo = models.ImageField(upload_to='restaurants/settings/logos/', blank=True, null=True)
    primary_color = models.CharField(max_length=20, default='#00E5FF')
    secondary_color = models.CharField(max_length=20, default='#081028')
    iva_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=19)
    tip_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=10)
    currency = models.CharField(max_length=10, default='COP')
    whatsapp_number = models.CharField(max_length=30, blank=True)
    address = models.TextField(blank=True)
    kitchen_printer_name = models.CharField(max_length=120, blank=True)
    cashier_printer_name = models.CharField(max_length=120, blank=True)
    enable_auto_print = models.BooleanField(default=False)
    auto_print_kitchen = models.BooleanField(default=True)
    auto_print_cashier = models.BooleanField(default=True)
    kitchen_ticket_width = models.CharField(max_length=2, choices=TICKET_WIDTH_CHOICES, default=TICKET_WIDTH_80)
    cashier_ticket_width = models.CharField(max_length=2, choices=TICKET_WIDTH_CHOICES, default=TICKET_WIDTH_80)
    enable_qr_orders = models.BooleanField(default=True)
    enable_tips = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Ajustes de {self.restaurant.name}'
