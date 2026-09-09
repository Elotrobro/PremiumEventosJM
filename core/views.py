from django.shortcuts import render

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


def testimonios(request):
    # Testimonios de clientes. Están escritos directamente en el HTML
    # (no existe un modelo Testimonio); para agregar/editar uno hay que
    # modificar core/templates/testimonios.html.
    return render(request, 'testimonios.html')


def galeria(request):
    # Galería de fotos de eventos anteriores, con modales de detalle.
    return render(request, 'galeria.html')


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
