import os

from django.core.files import File
from django.core.management.base import BaseCommand

from core.galeria_data import CATEGORIAS, EXTENSIONES_VALIDAS
from Bd_PremiumEventos.models import FotoGaleria


class Command(BaseCommand):
    """
    Migración única: copia a /media (y registra en la tabla foto_galeria)
    las fotos que hoy están a mano en core/static/images/galeria/<categoria>/,
    de cuando la galería todavía no tenía panel de administración.

    Los archivos originales en core/static/ NO se tocan ni se borran (por
    si algo sale mal); una vez verificado que la galería del sitio se ve
    bien desde la base de datos, esa carpeta se puede borrar a mano.

    Es seguro correrlo más de una vez: una foto que ya fue migrada (mismo
    nombre de archivo en la misma categoría) no se vuelve a duplicar.

        python manage.py migrar_fotos_galeria
    """
    help = 'Copia a /media las fotos de core/static/images/galeria/ y las registra en FotoGaleria.'

    def handle(self, *args, **options):
        base = os.path.join('core', 'static', 'images', 'galeria')
        total_migradas = 0
        total_omitidas = 0

        for categoria in CATEGORIAS:
            slug = categoria['slug']
            carpeta = os.path.join(base, slug)
            if not os.path.isdir(carpeta):
                continue

            ya_migradas = set(
                FotoGaleria.objects.filter(categoria=slug).values_list('imagen', flat=True)
            )

            archivos = sorted(
                nombre for nombre in os.listdir(carpeta)
                if os.path.splitext(nombre)[1].lower() in EXTENSIONES_VALIDAS
            )
            for nombre in archivos:
                ruta_destino = f'galeria/{slug}/{nombre}'
                if ruta_destino in ya_migradas:
                    total_omitidas += 1
                    continue

                ruta_origen = os.path.join(carpeta, nombre)
                with open(ruta_origen, 'rb') as archivo:
                    foto = FotoGaleria(categoria=slug)
                    foto.imagen.save(nombre, File(archivo), save=True)
                total_migradas += 1
                self.stdout.write(f'  + {slug}/{nombre}')

        self.stdout.write(self.style.SUCCESS(
            f'Listo: {total_migradas} foto(s) migrada(s), {total_omitidas} ya estaban migradas.'
        ))
