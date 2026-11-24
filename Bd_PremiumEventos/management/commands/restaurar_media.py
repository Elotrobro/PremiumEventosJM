import os
import shutil

from django.conf import settings
from django.core.management.base import BaseCommand

from Bd_PremiumEventos.media import ruta_original
from Bd_PremiumEventos.models import FotoGaleria, FotoSalon, ItemDecoracion


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
        # Los archivos de origen los busca ruta_original (Bd_PremiumEventos/media.py).
        grupos = [
            ('galería', FotoGaleria.objects.all()),
            ('catálogo', ItemDecoracion.objects.exclude(imagen='')),
            ('salones', FotoSalon.objects.all()),
        ]

        for etiqueta, registros in grupos:
            restauradas = 0
            faltantes = []
            for registro in registros:
                nombre = registro.imagen.name
                if not nombre:
                    continue
                destino = os.path.join(settings.MEDIA_ROOT, nombre)
                if os.path.isfile(destino):
                    continue
                origen = ruta_original(nombre)
                if origen is None:
                    faltantes.append(nombre)
                    continue
                os.makedirs(os.path.dirname(destino), exist_ok=True)
                shutil.copyfile(origen, destino)
                restauradas += 1

            self.stdout.write(f'{etiqueta}: {restauradas} restaurada(s), {len(faltantes)} sin archivo de origen')
            for nombre in faltantes:
                self.stdout.write(f'  - falta {nombre} (súbela de nuevo desde el panel)')
