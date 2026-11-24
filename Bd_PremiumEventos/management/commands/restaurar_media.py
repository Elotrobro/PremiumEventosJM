import os
import re
import shutil

from django.conf import settings
from django.core.management.base import BaseCommand

from Bd_PremiumEventos.models import FotoGaleria, FotoSalon, ItemDecoracion


# Carpetas del repositorio de donde salieron originalmente las fotos que
# hoy están en /media (ver los comandos migrar_fotos_galeria y
# migrar_catalogo). Como sí están en GitHub, sirven para reconstruir /media
# en un servidor nuevo, donde la carpeta /media llega vacía.
CARPETA_ESTATICA = os.path.join(settings.BASE_DIR, 'core', 'static', 'images')
# Copia opcional de la carpeta /media de un PC, subida al repositorio con
# este nombre (para recuperar también las fotos de los salones).
CARPETA_RESPALDO = os.path.join(settings.BASE_DIR, 'media_respaldo')

# Cuando ya existe un archivo con el mismo nombre, Django le agrega un
# sufijo aleatorio de 7 caracteres (foto.png → foto_Ab12Cd3.png).
SUFIJO_DJANGO = re.compile(r'_[A-Za-z0-9]{7}(?=\.[^.]+$)')


def _candidatos(nombre_en_bd, carpeta_estatica):
    """Rutas posibles del archivo original, en orden de preferencia."""
    yield os.path.join(CARPETA_RESPALDO, nombre_en_bd)
    if carpeta_estatica:
        base = os.path.basename(nombre_en_bd)
        yield os.path.join(carpeta_estatica, base)
        yield os.path.join(carpeta_estatica, SUFIJO_DJANGO.sub('', base))


class Command(BaseCommand):
    """
    Vuelve a crear en MEDIA_ROOT los archivos de las fotos que la base de
    datos tiene registradas pero que no están en el disco del servidor.

    Pasa en Railway: la base de datos (Aiven) es la misma de los PCs del
    equipo, pero la carpeta /media está en .gitignore y el servidor arranca
    sin ella. Este comando la reconstruye con:
      - Galería: core/static/images/galeria/<categoria>/
      - Catálogo: core/static/images/catalogo_productos/
      - Cualquier foto (incluidos salones): media_respaldo/<misma ruta>, si
        se sube una copia de la carpeta /media del PC con ese nombre.

    No toca la base de datos ni sobreescribe archivos que ya existen, así
    que es seguro correrlo en cada despliegue (ver railway.json).

        python manage.py restaurar_media
    """
    help = 'Recupera en /media las fotos registradas en la base de datos que faltan en el disco.'

    def handle(self, *args, **options):
        grupos = [
            ('galería', FotoGaleria.objects.all(),
             lambda f: os.path.join(CARPETA_ESTATICA, 'galeria', f.categoria)),
            ('catálogo', ItemDecoracion.objects.exclude(imagen=''),
             lambda f: os.path.join(CARPETA_ESTATICA, 'catalogo_productos')),
            ('salones', FotoSalon.objects.all(), lambda f: None),
        ]

        for etiqueta, registros, carpeta_de in grupos:
            restauradas = 0
            faltantes = []
            for registro in registros:
                nombre = registro.imagen.name
                if not nombre:
                    continue
                destino = os.path.join(settings.MEDIA_ROOT, nombre)
                if os.path.isfile(destino):
                    continue
                origen = next(
                    (r for r in _candidatos(nombre, carpeta_de(registro)) if os.path.isfile(r)),
                    None,
                )
                if origen is None:
                    faltantes.append(nombre)
                    continue
                os.makedirs(os.path.dirname(destino), exist_ok=True)
                shutil.copyfile(origen, destino)
                restauradas += 1

            self.stdout.write(f'{etiqueta}: {restauradas} restaurada(s), {len(faltantes)} sin archivo de origen')
            for nombre in faltantes:
                self.stdout.write(f'  - falta {nombre} (súbela de nuevo desde el panel)')
