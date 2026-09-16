from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Bd_PremiumEventos', '0008_backfill_codigo_seguimiento'),
    ]

    operations = [
        # Recién aquí se agrega unique=True: la migración 0008 ya dejó un
        # código distinto en cada fila, así que esta restricción no puede
        # fallar por duplicados.
        migrations.AlterField(
            model_name='cotizacion',
            name='codigo_seguimiento',
            field=models.CharField(max_length=30, unique=True, blank=True),
        ),
    ]
