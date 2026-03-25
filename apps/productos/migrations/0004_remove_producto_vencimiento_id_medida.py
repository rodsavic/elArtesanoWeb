from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('productos', '0003_remove_producto_precio_pedidos_ya'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='producto',
            name='id_medida',
        ),
        migrations.RemoveField(
            model_name='producto',
            name='vencimiento',
        ),
    ]
