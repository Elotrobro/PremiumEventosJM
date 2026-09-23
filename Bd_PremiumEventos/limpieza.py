"""
Eliminación automática de cuentas de cliente que nunca cotizaron.

Regla: una cuenta con rol 'cliente' que a los DIAS_SIN_COTIZAR días de
haberse creado todavía no ha hecho ninguna cotización se elimina sola.
Nunca toca cuentas 'admin' ni 'empleado', ni clientes que ya cotizaron.

Se ejecuta sola como máximo una vez al día (ver ejecutar_si_toca, que se
llama desde login_view y desde el dashboard del panel). También se puede
correr a mano o desde un programador de tareas con:

    python manage.py limpiar_clientes_sin_cotizacion
"""

import math
from datetime import timedelta

from django.core.cache import cache
from django.db.models import Exists, OuterRef
from django.utils import timezone

from .models import Cotizacion, Usuario

DIAS_SIN_COTIZAR = 60

_CLAVE_ULTIMA_LIMPIEZA = 'limpieza_clientes_sin_cotizacion'
_SEGUNDOS_ENTRE_LIMPIEZAS = 60 * 60 * 24


def clientes_sin_cotizacion():
    """Clientes que todavía no tienen ninguna cotización (vencidos o no)."""
    return Usuario.objects.filter(rol=Usuario.ROL_CLIENTE).annotate(
        tiene_cotizacion=Exists(Cotizacion.objects.filter(cliente__usuario=OuterRef('pk')))
    ).filter(tiene_cotizacion=False)


def clientes_vencidos():
    limite = timezone.now() - timedelta(days=DIAS_SIN_COTIZAR)
    return clientes_sin_cotizacion().filter(fecha_creacion__lt=limite)


def dias_para_eliminar(usuario):
    """Días que le quedan a un cliente sin cotizaciones antes de eliminarse."""
    vence = usuario.fecha_creacion + timedelta(days=DIAS_SIN_COTIZAR)
    return max(0, math.ceil((vence - timezone.now()).total_seconds() / 86400))


def eliminar_clientes_vencidos():
    """Elimina los clientes vencidos y devuelve cuántos eran."""
    vencidos = clientes_vencidos()
    total = vencidos.count()
    if total:
        # .delete() sobre el queryset anotado no es posible en todos los
        # motores, así que se borra por id.
        Usuario.objects.filter(pk__in=list(vencidos.values_list('pk', flat=True))).delete()
    return total


def ejecutar_si_toca():
    """Corre la limpieza si no se ha corrido en las últimas 24 horas."""
    if cache.add(_CLAVE_ULTIMA_LIMPIEZA, True, _SEGUNDOS_ENTRE_LIMPIEZAS):
        eliminar_clientes_vencidos()
