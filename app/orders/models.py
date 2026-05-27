from django.db import models
from products.models import Product
from tables.models import RestaurantTable

class Order(models.Model):
    STATUS_CHOICES = [
        ('OPEN', 'Abierta'),
        ('PREPARING', 'Preparando'),
        ('READY', 'Lista'),
        ('PAID', 'Pagada'),
        ('CANCELLED', 'Cancelada'),
    ]

    table = models.ForeignKey(RestaurantTable, on_delete=models.PROTECT, related_name='orders')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='OPEN')
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tax = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Orden #{self.id} - {self.table.name}'


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    def __str__(self):
        return f'{self.quantity} x {self.product.name}'
