"""
Carga en la base de datos la tabla de precios que antes estaba escrita
en el código (views.py, modal.js y la herramienta del chatbot en n8n).

Se corrige de paso el tramo de 100 invitados: antes valía $5.800.000,
menos que el de 90 ($5.850.000), así que entre 91 y 99 invitados el
precio bajaba. Ahora es $6.430.000 (el de 90 + 10 × $58.000, la misma
tarifa por invitado adicional que se cobra después de 100).
"""

from decimal import Decimal

from django.db import migrations

TABLA_INICIAL = [
    (20, '1800000'),
    (30, '2600000'),
    (40, '3200000'),
    (50, '3900000'),
    (60, '4500000'),
    (70, '4900000'),
    (80, '5440000'),
    (90, '5850000'),
    (100, '6430000'),
]
TARIFA_INICIAL = '58000'


def cargar(apps, schema_editor):
    PaquetePrecio = apps.get_model('Bd_PremiumEventos', 'PaquetePrecio')
    ConfiguracionPrecios = apps.get_model('Bd_PremiumEventos', 'ConfiguracionPrecios')
    for invitados, precio in TABLA_INICIAL:
        PaquetePrecio.objects.get_or_create(invitados=invitados, defaults={'precio': Decimal(precio)})
    ConfiguracionPrecios.objects.get_or_create(pk=1, defaults={'tarifa_invitado_adicional': Decimal(TARIFA_INICIAL)})


def borrar(apps, schema_editor):
    apps.get_model('Bd_PremiumEventos', 'PaquetePrecio').objects.all().delete()
    apps.get_model('Bd_PremiumEventos', 'ConfiguracionPrecios').objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('Bd_PremiumEventos', '0017_tabla_precios'),
    ]

    operations = [
        migrations.RunPython(cargar, borrar),
    ]
