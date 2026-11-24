import os
import re

from django.conf import settings
from django.http import Http404
from django.views.static import serve


# ═══════════════════════════════════════════════════════════════════════
# Fotos de /media cuyo archivo no está en el servidor.
#
# La base de datos (Aiven) es la misma en Railway y en los PCs del equipo,
# pero la carpeta /media está en .gitignore: un servidor nuevo (o un PC
# recién clonado) arranca sin ella. Las fotos de la galería y del catálogo
# salieron originalmente de core/static/images/ (comandos
# migrar_fotos_galeria y migrar_catalogo), que sí está en GitHub, así que
# desde ahí se pueden recuperar.
# ═══════════════════════════════════════════════════════════════════════

CARPETA_ESTATICA = os.path.join(settings.BASE_DIR, 'core', 'static', 'images')
# Copia opcional de la carpeta /media de un PC, subida al repositorio con
# este nombre (para recuperar también las fotos de los salones).
CARPETA_RESPALDO = os.path.join(settings.BASE_DIR, 'media_respaldo')

# Cuando ya existe un archivo con el mismo nombre, Django le agrega un
# sufijo aleatorio de 7 caracteres (foto.png → foto_Ab12Cd3.png).
SUFIJO_DJANGO = re.compile(r'_[A-Za-z0-9]{7}(?=\.[^.]+$)')


def _carpeta_estatica(nombre):
    """Carpeta de core/static/images/ de donde salió la foto, o None."""
    partes = nombre.split('/')
    if len(partes) == 3 and partes[0] == 'galeria':      # galeria/<categoria>/<archivo>
        return os.path.join(CARPETA_ESTATICA, 'galeria', partes[1])
    if len(partes) == 2 and partes[0] == 'catalogo':     # catalogo/<archivo>
        return os.path.join(CARPETA_ESTATICA, 'catalogo_productos')
    return None


def ruta_original(nombre):
    """
    Ruta absoluta de una copia del archivo `nombre` (ruta relativa a
    MEDIA_ROOT, como imagen.name) fuera de /media, o None si no hay.
    Busca, en orden: media_respaldo/, y la carpeta de core/static/images/
    de donde salió la foto (con y sin el sufijo que agrega Django).
    """
    # Solo rutas relativas simples: nada de "..", "\" ni rutas absolutas.
    if not nombre or nombre.startswith('/') or '\\' in nombre or '..' in nombre.split('/'):
        return None
    candidatos = [os.path.join(CARPETA_RESPALDO, nombre)]
    carpeta = _carpeta_estatica(nombre)
    if carpeta:
        base = os.path.basename(nombre)
        candidatos += [os.path.join(carpeta, base), os.path.join(carpeta, SUFIJO_DJANGO.sub('', base))]
    return next((ruta for ruta in candidatos if os.path.isfile(ruta)), None)


def servir_media(request, path):
    """
    Sirve /media/<path>. Si el archivo no está en MEDIA_ROOT, entrega la
    copia original (ver ruta_original) en vez de un 404, así las fotos se
    ven aunque /media no se haya restaurado en el servidor.
    """
    try:
        return serve(request, path, document_root=settings.MEDIA_ROOT)
    except Http404:
        original = ruta_original(path)
        if original is None:
            raise
        carpeta, archivo = os.path.split(original)
        return serve(request, archivo, document_root=carpeta)
