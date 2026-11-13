from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Bd_PremiumEventos', '0020_salones'),
    ]

    operations = [
        migrations.AddField(
            model_name='salon',
            name='direccion',
            field=models.CharField(blank=True, help_text='Dirección para el mapa. Ej.: Cl. 36 #70-19, San Antonio de Prado, Medellín, Antioquia.', max_length=255),
        ),
    ]
