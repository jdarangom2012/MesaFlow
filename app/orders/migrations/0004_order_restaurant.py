import django.db.models.deletion
from django.db import migrations, models


def populate_order_restaurants(apps, schema_editor):
    Order = apps.get_model('orders', 'Order')

    for order in Order.objects.select_related('table__restaurant'):
        order.restaurant_id = order.table.restaurant_id
        order.save(update_fields=['restaurant'])


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0003_alter_order_status'),
        ('restaurants', '0002_restaurant_branding_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='restaurant',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='orders', to='restaurants.restaurant'),
        ),
        migrations.RunPython(populate_order_restaurants, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='order',
            name='restaurant',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='orders', to='restaurants.restaurant'),
        ),
    ]
