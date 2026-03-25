from django.db import migrations


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.RunSQL(
            sql="""
            DROP TABLE IF EXISTS public.proveedores CASCADE;
            DROP SEQUENCE IF EXISTS public.proveedores_id_proveedor_seq CASCADE;
            """,
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]
