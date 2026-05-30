from django.db import migrations, models


def promote_superusers(apps, schema_editor):
    UserRestaurant = apps.get_model('accounts', 'UserRestaurant')

    UserRestaurant.objects.filter(user__is_superuser=True).update(role='SUPERADMIN')


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='userrestaurant',
            name='role',
            field=models.CharField(
                choices=[
                    ('SUPERADMIN', 'Superadmin SaaS'),
                    ('ADMIN', 'Admin restaurante'),
                    ('CAJERO', 'Cajero'),
                    ('COCINA', 'Cocina'),
                    ('MESERO', 'Mesero'),
                ],
                default='ADMIN',
                max_length=20,
            ),
        ),
        migrations.RunPython(promote_superusers, migrations.RunPython.noop),
    ]
