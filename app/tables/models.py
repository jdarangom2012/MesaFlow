from django.db import models
from restaurants.models import Restaurant

class RestaurantTable(models.Model):
    TYPE_SALON = 'SALON'
    TYPE_TERRACE = 'TERRACE'
    TYPE_VIP = 'VIP'
    TYPE_BAR = 'BAR'

    STATUS_CHOICES = [
        ('FREE', 'Libre'),
        ('OCCUPIED', 'Ocupada'),
        ('RESERVED', 'Reservada'),
        ('PAYMENT_PENDING', 'Pago pendiente'),
    ]
    TYPE_CHOICES = [
        (TYPE_SALON, 'Salón'),
        (TYPE_TERRACE, 'Terraza'),
        (TYPE_VIP, 'VIP'),
        (TYPE_BAR, 'Barra'),
    ]

    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name='tables')
    name = models.CharField(max_length=50)
    capacity = models.PositiveIntegerField(default=4)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default=TYPE_SALON)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='FREE')
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f'{self.restaurant.name} - {self.name}'
