import random
import string

from django.db import migrations


def _generar_codigo(fecha_str):
    sufijo = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f'PJM-{fecha_str}-{sufijo}'


def rellenar_codigos(apps, schema_editor):
    """
    Le asigna un código de seguimiento único a cada cotización que ya
    existía antes de este cambio (las nuevas lo reciben solas, ver
    Cotizacion.save() en models.py). Se usa la fecha de creación de cada
    fila para que el código quede fechado como si se hubiera generado en
    ese momento, en vez de mostrar la fecha en que se corrió esta migración.
    """
    Cotizacion = apps.get_model('Bd_PremiumEventos', 'Cotizacion')
    usados = set()
    for cotizacion in Cotizacion.objects.filter(codigo_seguimiento=''):
        fecha_str = cotizacion.fecha_evento.strftime('%Y%m%d') if cotizacion.fecha_evento else 'antiguo'
        codigo = _generar_codigo(fecha_str)
        while codigo in usados:
            codigo = _generar_codigo(fecha_str)
        usados.add(codigo)
        cotizacion.codigo_seguimiento = codigo
        cotizacion.save(update_fields=['codigo_seguimiento'])


def revertir(apps, schema_editor):
    # No hay nada sensato que "deshacer": simplemente se dejan los
    # códigos como están si algún día se revierte esta migración.
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('Bd_PremiumEventos', '0007_cotizacion_codigo_seguimiento_and_more'),
    ]

    operations = [
        migrations.RunPython(rellenar_codigos, revertir),
    ]
