from django.db import models

# Create your models here.
from django.db import models
from companies.models import Company

class Restaurant(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='restaurants')
    name = models.CharField(max_length=150)
    address = models.CharField(max_length=250, blank=True, null=True)
    phone = models.CharField(max_length=30, blank=True, null=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name