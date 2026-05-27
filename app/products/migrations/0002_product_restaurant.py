import django.db.models.deletion
from django.db import migrations, models


def populate_product_restaurants(apps, schema_editor):
    Product = apps.get_model('products', 'Product')

    for product in Product.objects.select_related('category__restaurant'):
        product.restaurant_id = product.category.restaurant_id
        product.save(update_fields=['restaurant'])


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0001_initial'),
        ('restaurants', '0002_restaurant_branding_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='restaurant',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='products', to='restaurants.restaurant'),
        ),
        migrations.RunPython(populate_product_restaurants, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='product',
            name='restaurant',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='products', to='restaurants.restaurant'),
        ),
    ]
