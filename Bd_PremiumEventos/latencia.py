"""
Cronómetro del guardado en la base de datos (time.perf_counter()).

Mide cuánto tarda la base de datos en guardar, editar o eliminar, y ese
tiempo se muestra abajo de la notificación verde, en letra pequeña y con
baja opacidad: "Guardado 38 ms". Solo lo ven el administrador y el
empleado; los clientes ven la notificación igual que siempre.

Uso en una vista:

    from Bd_PremiumEventos.latencia import Cronometro

    with Cronometro() as crono:
        form.save()
    messages.success(request, 'Guardado correctamente.',
                     extra_tags=crono.etiqueta(request))

El mismo cronómetro se puede usar varias veces y suma los tiempos. Sirve
para medir solo la base de datos dentro de un ciclo que también hace otra
cosa (ej. borrar el archivo de la foto en /media):

    crono = Cronometro()
    for foto in fotos:
        foto.imagen.delete(save=False)   # disco: no se cuenta
        with crono:
            foto.delete()                # base de datos: sí se cuenta

La etiqueta "latencia-bd=38.2" viaja en los extra_tags del mensaje;
core/templates/partials/_notificaciones.html la pasa en data-extra y
core/static/js/notificaciones.js la convierte en "Guardado 38 ms".
"""

import time

# Roles que ven el tiempo de guardado debajo de la notificación.
ROLES_CON_LATENCIA = ('admin', 'empleado')


def etiqueta_latencia(request, ms, otras=''):
    """
    extra_tags para messages: "latencia-bd=38.2" si quien está en la sesión
    es admin o empleado (si no, solo `otras`). `otras` son etiquetas que el
    mensaje ya tenía, ej. "registro-error".
    """
    partes = [otras] if otras else []
    if ms is not None and request.session.get('usuario_rol') in ROLES_CON_LATENCIA:
        partes.append(f'latencia-bd={ms:.1f}')
    return ' '.join(partes)


class Cronometro:
    """Suma el tiempo de cada bloque `with` en milisegundos (self.ms)."""

    def __init__(self):
        self.ms = None
        self._inicio = None

    def __enter__(self):
        self._inicio = time.perf_counter()
        return self

    def __exit__(self, *_error):
        transcurrido = (time.perf_counter() - self._inicio) * 1000
        self.ms = (self.ms or 0) + transcurrido
        return False   # si hubo un error, se deja pasar

    def etiqueta(self, request, otras=''):
        return etiqueta_latencia(request, self.ms, otras)
