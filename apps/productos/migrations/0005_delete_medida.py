from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('productos', '0004_remove_producto_vencimiento_id_medida'),
    ]

    operations = [
        migrations.DeleteModel(
            name='Medida',
        ),
    ]
