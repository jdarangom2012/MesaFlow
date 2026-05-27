from django.db import migrations, models
from django.utils import timezone
from django.utils.text import slugify


def populate_restaurant_slugs(apps, schema_editor):
    Restaurant = apps.get_model('restaurants', 'Restaurant')
    used_slugs = set()

    for restaurant in Restaurant.objects.order_by('id'):
        base_slug = slugify(restaurant.name) or f'restaurant-{restaurant.id}'
        slug = base_slug
        counter = 2

        while slug in used_slugs or Restaurant.objects.filter(slug=slug).exclude(id=restaurant.id).exists():
            slug = f'{base_slug}-{counter}'
            counter += 1

        restaurant.slug = slug
        restaurant.save(update_fields=['slug'])
        used_slugs.add(slug)


def populate_restaurant_created_at(apps, schema_editor):
    Restaurant = apps.get_model('restaurants', 'Restaurant')
    Restaurant.objects.filter(created_at__isnull=True).update(created_at=timezone.now())


class Migration(migrations.Migration):

    dependencies = [
        ('restaurants', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='restaurant',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
        migrations.AddField(
            model_name='restaurant',
            name='logo',
            field=models.ImageField(blank=True, null=True, upload_to='restaurants/logos/'),
        ),
        migrations.AddField(
            model_name='restaurant',
            name='primary_color',
            field=models.CharField(default='#00D4FF', max_length=20),
        ),
        migrations.AddField(
            model_name='restaurant',
            name='slug',
            field=models.SlugField(blank=True, max_length=160, null=True, unique=True),
        ),
        migrations.RunPython(populate_restaurant_slugs, migrations.RunPython.noop),
        migrations.RunPython(populate_restaurant_created_at, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='restaurant',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True),
        ),
        migrations.AlterField(
            model_name='restaurant',
            name='slug',
            field=models.SlugField(max_length=160, unique=True),
        ),
    ]
