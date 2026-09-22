from django.http import Http404
from django.shortcuts import render

from .galeria_data import (
    CATEGORIAS, categorias_por_grupo, fotos_de_categoria, mosaico_general,
    obtener_categoria,
)

# ═══════════════════════════════════════════════════════════════════════
# Vistas de la app `core`
#
# Todas son vistas "de solo lectura": no reciben datos (no procesan
# formularios ni tocan la base de datos), únicamente renderizan una
# plantilla estática. Por eso ninguna necesita el request.method ni
# lógica adicional: Django ya sabe resolver GET a estas rutas gracias a
# PremiumEventosJM/urls.py.
# ═══════════════════════════════════════════════════════════════════════


def inicio(request):
    # Página principal: carrusel + botón que abre el modal de cotización
    # (el formulario de ese modal SÍ tiene lógica, pero vive en
    # Bd_PremiumEventos.views.cotizacion_view, no aquí).
    return render(request, 'inicio.html')


def informacion(request):
    # Página "Sobre nosotros": texto institucional, sin datos dinámicos.
    return render(request, 'informacion.html')


def galeria(request):
    # Índice de la galería: el acordeón con los tipos de evento (menú de
    # navegación entre galerías) y un mosaico que mezcla fotos de todas
    # las categorías. Las fotos se leen de la tabla FotoGaleria, subidas
    # desde el panel de administrador (ver core/galeria_data.py).
    return render(request, 'galeria.html', {
        'grupos': categorias_por_grupo(),
        'total_categorias': len(CATEGORIAS),
        'fotos': mosaico_general(),
    })


def galeria_categoria(request, slug):
    # Galería de un solo tipo de evento (ej. /galeria/15-anos/): cabecera
    # con la foto de portada, mosaico completo y el acordeón al final para
    # saltar a otra galería.
    categoria = obtener_categoria(slug)
    if categoria is None:
        raise Http404('Esa galería no existe.')

    fotos, es_demo = fotos_de_categoria(slug)
    return render(request, 'galeria_categoria.html', {
        'categoria': categoria,
        'fotos': fotos,
        'total_fotos': len(fotos),
        'es_demo': es_demo,
        'portada': fotos[0]['url'] if fotos else '',
        'grupos': categorias_por_grupo(),
    })


def catalogo(request):
    # Catálogo de alquiler. Los productos están escritos directamente en
    # el HTML (ver comentario en core/templates/catalogo.html); el modelo
    # ItemDecoracion existe pero todavía no se usa desde aquí.
    return render(request, 'catalogo.html')


def convenios(request):
    # Salones y espacios aliados con los que trabaja la empresa.
    return render(request, 'convenios.html')


def contacto(request):
    # Formulario de contacto. ⚠️ Su <form> en el HTML todavía no envía
    # datos a ninguna vista (action="#"); falta crear la vista que reciba
    # el POST y lo guarde en el modelo ContactoSimple.
    return render(request, 'contacto.html')


# La vista de cotización ahora vive en Bd_PremiumEventos.views
# (cotizacion_view), porque necesita guardar la solicitud en las tablas
# Cliente / Cotizacion / DetalleCotizacion. Ver PremiumEventosJM/urls.py.

# La vista de login/logout también vive en Bd_PremiumEventos.views,
# porque es la que necesita consultar la tabla `usuario` de la base de datos.
# Ver PremiumEventosJM/urls.py para el enrutamiento.
