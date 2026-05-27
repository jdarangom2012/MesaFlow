from django.db import models

from django.contrib.auth.models import User

from restaurants.models import Restaurant


class UserRestaurant(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='restaurant_profile')
    restaurant = models.ForeignKey(Restaurant, on_delete=models.PROTECT, related_name='user_profiles', null=True, blank=True)

    def __str__(self):
        if self.restaurant:
            return f'{self.user.username} - {self.restaurant.name}'

        return self.user.username
