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
