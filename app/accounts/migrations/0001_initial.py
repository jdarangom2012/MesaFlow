import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


def create_profiles_for_existing_users(apps, schema_editor):
    User = apps.get_model('auth', 'User')
    Restaurant = apps.get_model('restaurants', 'Restaurant')
    UserRestaurant = apps.get_model('accounts', 'UserRestaurant')
    restaurant = Restaurant.objects.filter(is_active=True).order_by('id').first()

    if not restaurant:
        restaurant = Restaurant.objects.order_by('id').first()

    for user in User.objects.all():
        UserRestaurant.objects.get_or_create(user=user, defaults={'restaurant': restaurant})


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('restaurants', '0002_restaurant_branding_fields'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserRestaurant',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('restaurant', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='user_profiles', to='restaurants.restaurant')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='restaurant_profile', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.RunPython(create_profiles_for_existing_users, migrations.RunPython.noop),
    ]
