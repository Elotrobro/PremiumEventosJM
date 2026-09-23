import os

from django.core.files import File
from django.core.management.base import BaseCommand

from Bd_PremiumEventos.models import ItemDecoracion

# Mismos 32 productos, precios, unidades e imágenes que hoy están escritos
# a mano en core/templates/catalogo.html (data-categoria/data-nombre/
# data-precio/data-unidad de cada tarjeta) y en
# core/static/images/catalogo_productos/. El catálogo público (catalogo.html)
# sigue leyendo de ahí; esto es solo para poder gestionar estos mismos
# productos desde /panel-admin/catalogo/.
PRODUCTOS = [
    # ---- Mobiliario ----
    {'nombre': 'Silla', 'categoria': 'mobiliario', 'precio': 1500, 'unidad': 'Unidad', 'imagen': 'silla.png'},
    {'nombre': 'Silla Trono', 'categoria': 'mobiliario', 'precio': 100000, 'unidad': 'Unidad', 'imagen': 'silla_trono.png'},
    {'nombre': 'Mesas', 'categoria': 'mobiliario', 'precio': 8000, 'unidad': 'Unidad', 'imagen': 'mesas.png'},
    {'nombre': 'Mesa de Ruedas', 'categoria': 'mobiliario', 'precio': 35000, 'unidad': 'Unidad', 'imagen': 'mesa_de_ruedas.png'},
    {'nombre': 'Mesas Entorchadas', 'categoria': 'mobiliario', 'precio': 30000, 'unidad': 'Unidad', 'imagen': 'mesas_entorchadas.png'},
    {'nombre': 'Base Cuadra', 'categoria': 'mobiliario', 'precio': 5000, 'unidad': 'Unidad', 'imagen': 'base_cuadra.png'},
    {'nombre': 'Caballete', 'categoria': 'mobiliario', 'precio': 10000, 'unidad': 'Unidad', 'imagen': 'caballete.png'},

    # ---- Textiles y mantelería ----
    {'nombre': 'Mantel Blanco', 'categoria': 'textiles', 'precio': 8000, 'unidad': 'Unidad', 'imagen': 'mantel_blanco.png'},
    {'nombre': 'Sobre Mantel', 'categoria': 'textiles', 'precio': 5000, 'unidad': 'Variedad de colores', 'imagen': 'sobre_mantel.png'},
    {'nombre': 'Camino de Yute', 'categoria': 'textiles', 'precio': 3000, 'unidad': 'Por unidad', 'imagen': 'camino_de_yute.png'},
    {'nombre': 'Velos para Techo', 'categoria': 'textiles', 'precio': 20000, 'unidad': '75cm x 25mtrs', 'imagen': 'velos_para_techo.png'},
    {'nombre': 'Tapete Blanco', 'categoria': 'textiles', 'precio': 10000, 'unidad': 'Metro lineal', 'imagen': 'tapete_blanco.png'},
    {'nombre': 'Tapete Lila', 'categoria': 'textiles', 'precio': 10000, 'unidad': 'Metro lineal', 'imagen': 'tapete_lila.png'},
    {'nombre': 'Tapete Negro', 'categoria': 'textiles', 'precio': 10000, 'unidad': 'Metro lineal', 'imagen': 'tapete_negro.png'},
    {'nombre': 'Tapete Rojo', 'categoria': 'textiles', 'precio': 12000, 'unidad': 'Metro lineal', 'imagen': 'tapete_rojo.png'},
    {'nombre': 'Tapete Verde', 'categoria': 'textiles', 'precio': 10000, 'unidad': 'Metro lineal', 'imagen': 'tapete_verde.png'},
    {'nombre': 'Pañoleta Decorativa', 'categoria': 'textiles', 'precio': 1500, 'unidad': 'Unidad', 'imagen': 'panoleta.png'},
    {'nombre': 'Vestido de Silla', 'categoria': 'textiles', 'precio': 6000, 'unidad': 'Unidad', 'imagen': 'vestido_de_silla.png'},

    # ---- Decoración y ambientación ----
    {'nombre': 'Cilindros de Vidrio', 'categoria': 'decoracion', 'precio': 3000, 'unidad': 'Unidad', 'imagen': 'cilindros_vidrio.png'},
    {'nombre': 'Torre Eiffel (160cm)', 'categoria': 'decoracion', 'precio': 40000, 'unidad': 'Alto 160cms', 'imagen': 'torre_eiffel.png'},
    {'nombre': 'Aro Decorativo (1.50x1.50)', 'categoria': 'decoracion', 'precio': 40000, 'unidad': '1.50 x 1.50 cm', 'imagen': 'aro.png'},
    {'nombre': 'Backing Puerta y Marco', 'categoria': 'decoracion', 'precio': 150000, 'unidad': 'Unidad', 'imagen': 'baking_puerta_y_marco.png'},
    {'nombre': 'Baúl Decorativo', 'categoria': 'decoracion', 'precio': 25000, 'unidad': 'Unidad', 'imagen': 'baul.png'},
    {'nombre': 'Bola Tejida de Madera', 'categoria': 'decoracion', 'precio': 8000, 'unidad': 'Unidad', 'imagen': 'bola_tejida_madera.png'},
    {'nombre': 'Cilindros Blancos', 'categoria': 'decoracion', 'precio': 3000, 'unidad': 'Unidad', 'imagen': 'cilindros_blancos.png'},
    {'nombre': 'Hiedra', 'categoria': 'decoracion', 'precio': 5000, 'unidad': 'Metro lineal', 'imagen': 'hiedra.png'},
    {'nombre': 'Hiedra Blanca', 'categoria': 'decoracion', 'precio': 6000, 'unidad': 'Metro lineal', 'imagen': 'hiedra_blanca.png'},
    {'nombre': 'Letras Decorativas', 'categoria': 'decoracion', 'precio': 15000, 'unidad': 'Por letra', 'imagen': 'letras.png'},
    {'nombre': 'Mariposas Decorativas', 'categoria': 'decoracion', 'precio': 2000, 'unidad': 'Unidad', 'imagen': 'mariposa.png'},
    {'nombre': 'Números Decorativos', 'categoria': 'decoracion', 'precio': 15000, 'unidad': 'Por número', 'imagen': 'numeros.png'},
    {'nombre': 'Kit Quinceañero', 'categoria': 'decoracion', 'precio': 180000, 'unidad': 'Kit completo', 'imagen': 'quinceanero.png'},
    {'nombre': 'Rodajas de Madera', 'categoria': 'decoracion', 'precio': 4000, 'unidad': 'Unidad', 'imagen': 'rodajas_madera.png'},
]


class Command(BaseCommand):
    help = (
        'Migra a la base de datos (tabla item_decoracion) los 32 productos del catálogo de '
        'alquiler que hoy están escritos a mano en catalogo.html, junto con sus imágenes de '
        'core/static/images/catalogo_productos/. Es seguro correrlo más de una vez: si el '
        'producto ya existe (por nombre), solo actualiza sus datos y su imagen, no duplica filas.'
    )

    def handle(self, *args, **options):
        carpeta = os.path.join('core', 'static', 'images', 'catalogo_productos')
        creados = 0
        actualizados = 0

        for producto in PRODUCTOS:
            ruta_imagen = os.path.join(carpeta, producto['imagen'])
            item, creado = ItemDecoracion.objects.get_or_create(
                nombre=producto['nombre'],
                defaults={
                    'descripcion': f"Alquiler de {producto['nombre'].lower()} para tu evento.",
                    'precio': producto['precio'],
                    'categoria': producto['categoria'],
                    'unidad': producto['unidad'],
                    'estado': True,
                },
            )

            if not creado:
                item.precio = producto['precio']
                item.categoria = producto['categoria']
                item.unidad = producto['unidad']
                item.save()

            if not item.imagen and os.path.isfile(ruta_imagen):
                with open(ruta_imagen, 'rb') as archivo:
                    item.imagen.save(producto['imagen'], File(archivo), save=True)

            if creado:
                creados += 1
                self.stdout.write(f'  + {producto["nombre"]}')
            else:
                actualizados += 1

        self.stdout.write(self.style.SUCCESS(
            f'Listo: {creados} producto(s) nuevo(s), {actualizados} ya existían (se actualizaron sus datos).'
        ))
