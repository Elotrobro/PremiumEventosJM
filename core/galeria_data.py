"""
Catálogo de galerías por tipo de evento.

Las fotos NO viven en la base de datos: cada categoría muestra
automáticamente las imágenes que existan en

    core/static/images/galeria/<slug>/

Para publicar fotos nuevas basta con copiarlas en la carpeta de su
categoría; no hay que tocar el código ni el HTML. Mientras una carpeta
esté vacía, la galería usa imágenes de muestra del sitio y lo advierte
en pantalla (ver `es_demo` en `fotos_de_categoria`).
"""

import os

from django.contrib.staticfiles import finders
from django.templatetags.static import static
from PIL import Image

# Extensiones que se consideran fotos al leer la carpeta de una categoría
EXTENSIONES_VALIDAS = {'.jpg', '.jpeg', '.png', '.webp', '.avif', '.gif'}

# Proporciones (ancho/alto) que se reparten en ciclo entre las fotos de
# muestra para que el mosaico se vea variado como el de una galería real.
# Van como texto porque terminan dentro de un `aspect-ratio` de CSS, que
# siempre espera el punto decimal (nunca la coma del formato español).
PROPORCIONES_MUESTRA = ['0.7500', '1.0000', '0.8000', '1.3300', '0.7000', '1.0000', '0.8500', '1.5000']

# ─────────────────────────────────────────────────────────────────────────
# Las 12 categorías de la galería, agrupadas en los dos bloques del
# acordeón que sirve de menú de navegación entre galerías.
# ─────────────────────────────────────────────────────────────────────────
CATEGORIAS = [
    {
        'slug': 'matrimonio',
        'nombre': 'Matrimonio',
        'grupo': 'Celebraciones',
        'icono': 'fa-ring',
        'descripcion': 'Bodas soñadas con decoración, montaje y una atmósfera hecha para recordar toda la vida.',
    },
    {
        'slug': '15-anos',
        'nombre': '15 Años',
        'grupo': 'Celebraciones',
        'icono': 'fa-crown',
        'descripcion': 'Revive la magia de las fiestas de 15 años: decoración, shows y momentos únicos.',
    },
    {
        'slug': 'grados',
        'nombre': 'Grados',
        'grupo': 'Celebraciones',
        'icono': 'fa-graduation-cap',
        'descripcion': 'Celebraciones de grado que convierten el final de una etapa en una gran fiesta.',
    },
    {
        'slug': 'proms',
        'nombre': 'Proms',
        'grupo': 'Celebraciones',
        'icono': 'fa-glass-cheers',
        'descripcion': 'Fiestas de fin de grado con montaje, luces y ambientación de gala.',
    },
    {
        'slug': 'primera-comunion',
        'nombre': 'Primera Comunión',
        'grupo': 'Celebraciones',
        'icono': 'fa-dove',
        'descripcion': 'Primeras comuniones con una decoración sobria, luminosa y llena de detalles.',
    },
    {
        'slug': 'bautizo',
        'nombre': 'Bautizo',
        'grupo': 'Celebraciones',
        'icono': 'fa-pray',
        'descripcion': 'Bautizos íntimos y elegantes para celebrar en familia el primer gran día.',
    },
    {
        'slug': 'fiesta-infantil',
        'nombre': 'Fiesta infantil',
        'grupo': 'Momentos y servicios',
        'icono': 'fa-ice-cream',
        'descripcion': 'Fiestas infantiles temáticas, coloridas y pensadas para que los niños no paren de jugar.',
    },
    {
        'slug': 'cumpleanos',
        'nombre': 'Cumpleaños',
        'grupo': 'Momentos y servicios',
        'icono': 'fa-birthday-cake',
        'descripcion': 'Cumpleaños de todas las edades con montaje, torta, música y decoración a la medida.',
    },
    {
        'slug': 'baby-shower',
        'nombre': 'Baby shower',
        'grupo': 'Momentos y servicios',
        'icono': 'fa-baby-carriage',
        'descripcion': 'Baby showers acogedores, con ambientación suave y detalles para consentir a mamá.',
    },
    {
        'slug': 'revelacion-de-genero',
        'nombre': 'Revelación de género',
        'grupo': 'Momentos y servicios',
        'icono': 'fa-heart',
        'descripcion': 'El momento de la revelación, con montaje y efectos que hacen estallar la sorpresa.',
    },
    {
        'slug': 'fiesta-empresarial',
        'nombre': 'Fiesta empresarial',
        'grupo': 'Momentos y servicios',
        'icono': 'fa-briefcase',
        'descripcion': 'Eventos corporativos, integraciones y fiestas de fin de año con producción completa.',
    },
    {
        'slug': 'alquiler-de-mobiliario',
        'nombre': 'Alquiler de mobiliario',
        'grupo': 'Momentos y servicios',
        'icono': 'fa-chair',
        'descripcion': 'Mesas, sillas, tronos, textiles y piezas decorativas listas para tu evento.',
    },
]

# Fotos que se usan como vista previa mientras una categoría todavía no
# tiene su propia carpeta con imágenes reales.
FOTOS_DE_MUESTRA = [
    'images/CarruselGa.png',
    'images/CarruselGa2.png',
    'images/CarruselGa3.png',
    'images/CarruselGa4.png',
    'images/CarruselGa5.png',
    'images/Carrusel11.png',
    'images/Carrusel2.png',
    'images/Carrusel3.png',
    'images/Trono.png',
    'images/Trono2.png',
]

# Caché en memoria de las proporciones ya leídas de cada archivo, para no
# volver a abrir la imagen en cada request. La clave incluye la fecha de
# modificación, así que si se reemplaza una foto la proporción se recalcula.
_cache_proporciones = {}


def _proporcion(ruta_absoluta):
    """
    Devuelve el ancho/alto real de una foto como texto, para que el
    mosaico reserve el espacio exacto de cada imagen antes de bajarla
    (así el diseño no salta mientras las fotos van cargando).
    """
    clave = (ruta_absoluta, os.path.getmtime(ruta_absoluta))
    if clave not in _cache_proporciones:
        with Image.open(ruta_absoluta) as imagen:
            ancho, alto = imagen.size
        _cache_proporciones[clave] = f'{ancho / alto:.4f}'
    return _cache_proporciones[clave]


def categorias_por_grupo():
    """Agrupa las categorías en el orden en que se muestran en el acordeón."""
    grupos = {}
    for categoria in CATEGORIAS:
        grupos.setdefault(categoria['grupo'], []).append(categoria)
    return grupos


def obtener_categoria(slug):
    """Busca una categoría por su slug; None si no existe."""
    return next((c for c in CATEGORIAS if c['slug'] == slug), None)


def fotos_de_categoria(slug):
    """
    Devuelve (fotos, es_demo) para una categoría.

    `fotos` es una lista de diccionarios {url, proporcion} lista para el
    mosaico; `es_demo` indica que la carpeta de la categoría todavía está
    vacía y se están mostrando imágenes de muestra del sitio.
    """
    carpeta = finders.find(f'images/galeria/{slug}')

    if carpeta and os.path.isdir(carpeta):
        archivos = sorted(
            nombre for nombre in os.listdir(carpeta)
            if os.path.splitext(nombre)[1].lower() in EXTENSIONES_VALIDAS
        )
        if archivos:
            fotos = [
                {
                    'url': static(f'images/galeria/{slug}/{nombre}'),
                    'proporcion': _proporcion(os.path.join(carpeta, nombre)),
                }
                for nombre in archivos
            ]
            return fotos, False

    # Sin fotos propias todavía: vista previa con imágenes del sitio. Cada
    # categoría arranca la lista de muestra en una posición distinta para
    # que las galerías no se vean todas idénticas entre sí ni el mosaico
    # del índice termine repitiendo la misma foto doce veces.
    posicion = next((i for i, c in enumerate(CATEGORIAS) if c['slug'] == slug), 0)
    desplazamiento = (posicion * 3) % len(FOTOS_DE_MUESTRA)
    muestras = FOTOS_DE_MUESTRA[desplazamiento:] + FOTOS_DE_MUESTRA[:desplazamiento]

    fotos = [
        {
            'url': static(ruta),
            'proporcion': PROPORCIONES_MUESTRA[indice % len(PROPORCIONES_MUESTRA)],
        }
        for indice, ruta in enumerate(muestras)
    ]
    return fotos, True


def mosaico_general(por_categoria=2):
    """
    Mezcla las primeras fotos de todas las categorías para el mosaico de
    portada del índice de la galería. Se descartan las repetidas, así que
    mientras las categorías usen imágenes de muestra el mosaico no se
    llena con la misma foto una y otra vez.
    """
    mezcla = []
    vistas = set()
    for categoria in CATEGORIAS:
        fotos, _es_demo = fotos_de_categoria(categoria['slug'])
        for foto in fotos[:por_categoria]:
            if foto['url'] in vistas:
                continue
            vistas.add(foto['url'])
            mezcla.append({**foto, 'categoria': categoria['nombre'], 'slug': categoria['slug']})
    return mezcla
