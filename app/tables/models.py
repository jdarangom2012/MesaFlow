from django.db import models

# Create your models here.
from django.db import models
from restaurants.models import Restaurant

class RestaurantTable(models.Model):
    STATUS_CHOICES = [
        ('FREE', 'Libre'),
        ('OCCUPIED', 'Ocupada'),
        ('RESERVED', 'Reservada'),
        ('CLOSED', 'Cerrada'),
    ]

    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name='tables')
    name = models.CharField(max_length=50)
    capacity = models.PositiveIntegerField(default=4)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='FREE')

    def __str__(self):
        return f'{self.restaurant.name} - {self.name}'