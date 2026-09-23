import json
from datetime import datetime, timedelta

from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Sum, Count, Exists, OuterRef
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone

from Bd_PremiumEventos.models import (
    Usuario, ContactoSimple, ItemDecoracion, Cotizacion, DetalleCotizacion, FotoGaleria,Testimonio
)
from Bd_PremiumEventos import limpieza
from core.galeria_data import CATEGORIAS
from .decorators import admin_required, staff_required, es_admin
from .forms import UsuarioAdminForm, ItemDecoracionForm, CotizacionEstadoForm, SubirFotosGaleriaForm
from .utils import formatear_miles

# ═══════════════════════════════════════════════════════════════════════
# Panel de administrador a medida (no es el admin genérico de Django).
#
# Todas las vistas están protegidas con @staff_required (rol 'admin' o
# 'empleado') o, en las acciones que 'empleado' tiene prohibidas, con
# @admin_required. Usan plantillas propias que extienden
# panel_admin/base_admin.html para mantener el estilo del sitio.
#
# Resumen de lo que NO puede hacer un 'empleado' (ver es_admin() y los
# comentarios en cada vista):
#   - Eliminar nada, EXCEPTO usuarios con rol 'cliente' que todavía no
#     hayan hecho ninguna cotización.
#   - Editar una cotización (solo puede verla completa) ni editar
#     ningún usuario (ni clientes ni otras cuentas de staff).
#   - Crear un usuario con rol 'admin' o 'empleado' (solo 'cliente'; ver
#     UsuarioAdminForm.__init__).
# ═══════════════════════════════════════════════════════════════════════

# Ventana de "Novedades" del dashboard: por defecto y como máximo
# sugerido, 14 días (2 semanas), pero se puede pedir otra con ?dias=N
# (ver _dias_novedades). DIAS_NOVEDADES_OPCIONES son los atajos que se
# muestran como botones en la plantilla.
DIAS_NOVEDADES_DEFECTO = 14
DIAS_NOVEDADES_OPCIONES = [7, 14, 30]
DIAS_NOVEDADES_MINIMO = 1
DIAS_NOVEDADES_MAXIMO = 90


def _dias_novedades(request):
    """Lee y valida el ?dias= de la querystring, con el tope 1-90 días."""
    try:
        dias = int(request.GET.get('dias', DIAS_NOVEDADES_DEFECTO))
    except (TypeError, ValueError):
        dias = DIAS_NOVEDADES_DEFECTO
    return max(DIAS_NOVEDADES_MINIMO, min(dias, DIAS_NOVEDADES_MAXIMO))


@staff_required
def dashboard(request):
    limpieza.ejecutar_si_toca()  # clientes sin cotizar en 60 días (ver Bd_PremiumEventos/limpieza.py)
    dias = _dias_novedades(request)
    ahora = timezone.now()
    hoy = timezone.localdate()

    contexto = {
        'total_usuarios': Usuario.objects.count(),
        'total_cotizaciones': Cotizacion.objects.count(),
        'cotizaciones_pendientes': Cotizacion.objects.filter(estado=Cotizacion.ESTADO_PENDIENTE).count(),
        'total_mensajes': ContactoSimple.objects.count(),
        'total_items': ItemDecoracion.objects.count(),

        # ── Novedades: recuerdan al admin/empleado lo que pasó recientemente
        # y lo que se viene, cada vez que entra al panel (ver dashboard.html).
        'dias_novedades': dias,
        'dias_opciones': DIAS_NOVEDADES_OPCIONES,
        'cotizaciones_recientes': DetalleCotizacion.objects.select_related('cotizacion', 'cotizacion__cliente')
            .filter(fecha_cotizacion__gte=ahora - timedelta(days=dias))
            .order_by('-fecha_cotizacion')[:8],
        'eventos_proximos': Cotizacion.objects.select_related('cliente')
            .filter(fecha_evento__gte=hoy, fecha_evento__lte=hoy + timedelta(days=dias))
            .order_by('fecha_evento')[:8],
    }
    return render(request, 'panel_admin/dashboard.html', contexto)


# ───────────────────────────── Usuarios ─────────────────────────────

@staff_required
def usuarios_list(request):
    # tiene_cotizacion se anota para que la plantilla sepa, sin consultas
    # extra por fila, a qué clientes puede eliminar un 'empleado' (solo
    # los que todavía no han hecho ninguna cotización).
    usuarios = list(Usuario.objects.annotate(
        tiene_cotizacion=Exists(Cotizacion.objects.filter(cliente__usuario=OuterRef('pk')))
    ).order_by('nombre_completo'))
    # Días que le quedan a cada cliente sin cotizaciones antes de que el
    # sistema lo elimine solo (ver Bd_PremiumEventos/limpieza.py).
    for usuario in usuarios:
        if usuario.rol == Usuario.ROL_CLIENTE and not usuario.tiene_cotizacion:
            usuario.dias_para_eliminar = limpieza.dias_para_eliminar(usuario)
    return render(request, 'panel_admin/usuarios_list.html', {
        'usuarios': usuarios,
        'dias_sin_cotizar': limpieza.DIAS_SIN_COTIZAR,
    })


@staff_required
def usuario_create(request):
    # Un 'empleado' puede crear usuarios, pero el formulario le oculta la
    # posibilidad de asignar rol admin/empleado (ver UsuarioAdminForm).
    actor_rol = request.session.get('usuario_rol')
    if request.method == 'POST':
        form = UsuarioAdminForm(request.POST, actor_rol=actor_rol)
        if form.is_valid():
            form.save()
            messages.success(request, 'Usuario creado correctamente.')
            return redirect('panel_admin:usuarios_list')
    else:
        form = UsuarioAdminForm(actor_rol=actor_rol)
    return render(request, 'panel_admin/usuario_form.html', {'form': form, 'modo': 'crear'})


@admin_required
def usuario_edit(request, pk):
    # Solo admin: un 'empleado' no puede editar ninguna cuenta (ni
    # clientes ni otro staff) — así se lo pidieron explícitamente para
    # los clientes, y se extiende a cualquier usuario porque dejar que un
    # empleado cambie la contraseña o el rol de otra cuenta de staff
    # sería una puerta abierta a que se dé permisos a sí mismo.
    usuario = get_object_or_404(Usuario, pk=pk)
    if request.method == 'POST':
        form = UsuarioAdminForm(request.POST, instance=usuario, actor_rol='admin')
        if form.is_valid():
            form.save()
            messages.success(request, 'Usuario actualizado correctamente.')
            return redirect('panel_admin:usuarios_list')
    else:
        form = UsuarioAdminForm(instance=usuario, actor_rol='admin')
    return render(request, 'panel_admin/usuario_form.html', {'form': form, 'modo': 'editar', 'usuario': usuario})


@staff_required
def usuario_delete(request, pk):
    usuario = get_object_or_404(Usuario, pk=pk)

    # Un 'empleado' solo puede eliminar clientes que todavía no hayan
    # hecho ninguna cotización (pedido explícito). Cualquier otro caso
    # (otro rol, o un cliente que ya cotizó) queda bloqueado aquí, no
    # solo oculto en la plantilla, por si alguien arma el POST a mano.
    if not es_admin(request):
        tiene_cotizacion = Cotizacion.objects.filter(cliente__usuario=usuario).exists()
        if usuario.rol != Usuario.ROL_CLIENTE or tiene_cotizacion:
            messages.error(request, 'Como empleado, solo puedes eliminar clientes que aún no hayan hecho ninguna cotización.')
            return redirect('panel_admin:usuarios_list')

    if request.method == 'POST':
        if usuario.pk == request.session.get('usuario_id'):
            messages.error(request, 'No puedes eliminar tu propio usuario mientras tienes la sesión activa.')
            return redirect('panel_admin:usuarios_list')
        usuario.delete()
        messages.success(request, 'Usuario eliminado correctamente.')
        return redirect('panel_admin:usuarios_list')
    return render(request, 'panel_admin/confirmar_eliminar.html', {
        'objeto': usuario, 'titulo': 'usuario', 'cancelar_url': 'panel_admin:usuarios_list',
    })


# ─────────────────── Catálogo de decoración (ItemDecoracion) ───────────────────

@staff_required
def catalogo_list(request):
    items = ItemDecoracion.objects.all().order_by('nombre')
    return render(request, 'panel_admin/catalogo_list.html', {'items': items})


@staff_required
def catalogo_create(request):
    if request.method == 'POST':
        form = ItemDecoracionForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Ítem de decoración creado correctamente.')
            return redirect('panel_admin:catalogo_list')
    else:
        form = ItemDecoracionForm()
    return render(request, 'panel_admin/catalogo_form.html', {'form': form, 'modo': 'crear'})


@staff_required
def catalogo_edit(request, pk):
    item = get_object_or_404(ItemDecoracion, pk=pk)
    if request.method == 'POST':
        form = ItemDecoracionForm(request.POST, request.FILES, instance=item)
        if form.is_valid():
            form.save()
            messages.success(request, 'Ítem de decoración actualizado correctamente.')
            return redirect('panel_admin:catalogo_list')
    else:
        form = ItemDecoracionForm(instance=item)
    return render(request, 'panel_admin/catalogo_form.html', {'form': form, 'modo': 'editar', 'item': item})


@admin_required  # 'empleado' no puede eliminar nada salvo clientes sin cotizaciones (ver usuario_delete)
def catalogo_delete(request, pk):
    item = get_object_or_404(ItemDecoracion, pk=pk)
    if request.method == 'POST':
        if item.imagen:
            item.imagen.delete(save=False)  # borra también el archivo en /media, no solo el registro
        item.delete()
        messages.success(request, 'Ítem de decoración eliminado correctamente.')
        return redirect('panel_admin:catalogo_list')
    return render(request, 'panel_admin/confirmar_eliminar.html', {
        'objeto': item, 'titulo': 'ítem de decoración', 'cancelar_url': 'panel_admin:catalogo_list',
    })


# ─────────────────── Galería (FotoGaleria) ───────────────────
#
# Fotos que se muestran en /galeria/ y /galeria/<slug>/ (ver
# core/galeria_data.py). Antes había que copiar los archivos a mano en
# core/static/images/galeria/<categoria>/; ahora se suben aquí y quedan
# en /media, servidas por FotoGaleria.imagen.

@staff_required
def galeria_list(request):
    fotos_por_categoria = [
        {**categoria, 'fotos': FotoGaleria.objects.filter(categoria=categoria['slug'])}
        for categoria in CATEGORIAS
    ]
    form = SubirFotosGaleriaForm()
    return render(request, 'panel_admin/galeria_list.html', {
        'fotos_por_categoria': fotos_por_categoria,
        'form': form,
    })


@staff_required
def galeria_upload(request):
    if request.method == 'POST':
        form = SubirFotosGaleriaForm(request.POST, request.FILES)
        if form.is_valid():
            categoria = form.cleaned_data['categoria']
            for imagen in form.cleaned_data['imagenes']:
                FotoGaleria.objects.create(categoria=categoria, imagen=imagen)
            total = len(form.cleaned_data['imagenes'])
            messages.success(request, f'{total} foto{"s" if total != 1 else ""} subida{"s" if total != 1 else ""} correctamente.')
        else:
            errores = ' '.join(e for lista in form.errors.values() for e in lista)
            messages.error(request, f'No se subió ninguna foto. {errores}')
    return redirect('panel_admin:galeria_list')


@admin_required  # 'empleado' no puede eliminar nada salvo clientes sin cotizaciones (ver usuario_delete)
def galeria_delete(request, pk):
    foto = get_object_or_404(FotoGaleria, pk=pk)
    if request.method == 'POST':
        foto.imagen.delete(save=False)  # borra también el archivo en /media, no solo el registro
        foto.delete()
        messages.success(request, 'Foto eliminada correctamente.')
        return redirect('panel_admin:galeria_list')
    return render(request, 'panel_admin/confirmar_eliminar.html', {
        'objeto': foto, 'titulo': 'foto de la galería', 'cancelar_url': 'panel_admin:galeria_list',
    })


# ─────────────────── Mensajes de contacto (ContactoSimple) ───────────────────

@staff_required
def mensajes_list(request):
    mensajes = ContactoSimple.objects.all().order_by('-fecha_contacto')
    return render(request, 'panel_admin/mensajes_list.html', {'mensajes': mensajes})


@admin_required  # 'empleado' no puede eliminar nada salvo clientes sin cotizaciones (ver usuario_delete)
def mensaje_delete(request, pk):
    mensaje = get_object_or_404(ContactoSimple, pk=pk)
    if request.method == 'POST':
        mensaje.delete()
        messages.success(request, 'Mensaje eliminado correctamente.')
        return redirect('panel_admin:mensajes_list')
    return render(request, 'panel_admin/confirmar_eliminar.html', {
        'objeto': mensaje, 'titulo': 'mensaje de contacto', 'cancelar_url': 'panel_admin:mensajes_list',
    })


# ───────────────────────────── Testimonios ─────────────────────────────

@staff_required
def testimonios_list(request):
    testimonios = Testimonio.objects.select_related(
        'usuario'
    ).order_by('-fecha_creacion')

    return render(
        request,
        'panel_admin/testimonios_list.html',
        {
            'testimonios': testimonios,
        }
    )


@staff_required
def testimonio_aprobar(request, pk):
    """
    Lo usa la casilla "Aprobado" de cada fila del listado: al marcarla o
    desmarcarla se envía este POST y se guarda al instante. Los testimonios
    no se crean ni se editan desde el panel (son la opinión del cliente);
    solo se decide si se publican en /testimonios/ o no.
    """
    testimonio = get_object_or_404(Testimonio, pk=pk)
    if request.method == 'POST':
        testimonio.aprobado = request.POST.get('aprobado') == 'on'
        testimonio.save(update_fields=['aprobado'])
        estado = 'aprobado y publicado' if testimonio.aprobado else 'marcado como no aprobado (ya no se publica)'
        messages.success(request, f'Testimonio de {testimonio.usuario.nombre_completo} {estado}.')
    return redirect('panel_admin:testimonios_list')


@admin_required
def testimonio_delete(request, pk):
    testimonio = get_object_or_404(
        Testimonio,
        pk=pk
    )

    if request.method == 'POST':
        testimonio.delete()

        messages.success(
            request,
            'Testimonio eliminado correctamente.'
        )

        return redirect('panel_admin:testimonios_list')

    return render(
        request,
        'panel_admin/confirmar_eliminar.html',
        {
            'objeto': testimonio,
            'titulo': 'testimonio',
            'cancelar_url': 'panel_admin:testimonios_list',
        }
    )


# ───────────────────────────── Cotizaciones ─────────────────────────────

@staff_required
def cotizaciones_list(request):
    cotizaciones = Cotizacion.objects.select_related('cliente')
    cotizaciones, contexto_filtro = _filtrar_cotizaciones(
        request, cotizaciones, 'detallecotizacion__fecha_cotizacion', 'estado',
    )
    return render(request, 'panel_admin/cotizaciones_list.html', {
        'cotizaciones': cotizaciones.distinct().order_by('-id_cotizacion'),
        **contexto_filtro,
    })


@staff_required
def cotizacion_edit(request, pk):
    """
    Muestra el detalle completo de la cotización a admin y empleado por
    igual (antes faltaban los servicios solicitados, observaciones, etc.
    — quedaban solo en el JSON de DetalleCotizacion.detalles sin
    mostrarse en ningún lado). El formulario de estado/notas (el botón
    "Validar") solo se procesa si quien está autenticado es admin: un
    empleado puede ver esta pantalla completa, pero no cambiar nada en
    ella (se bloquea aquí, no solo ocultando el formulario en la
    plantilla, por si alguien arma el POST a mano).
    """
    cotizacion = get_object_or_404(Cotizacion, pk=pk)
    detalle = cotizacion.detallecotizacion_set.first()

    detalles_extra = {}
    if detalle and detalle.detalles:
        try:
            detalles_extra = json.loads(detalle.detalles)
        except (TypeError, ValueError):
            detalles_extra = {}

    if request.method == 'POST':
        if not es_admin(request):
            return HttpResponseForbidden('Solo un administrador puede validar el estado de una cotización.')
        form = CotizacionEstadoForm(request.POST, instance=cotizacion)
        if form.is_valid():
            form.save()
            messages.success(request, 'Cotización validada correctamente.')
            return redirect('panel_admin:cotizaciones_list')
    else:
        form = CotizacionEstadoForm(instance=cotizacion)

    return render(request, 'panel_admin/cotizacion_form.html', {
        'form': form,
        'cotizacion': cotizacion,
        'detalle': detalle,
        'detalles_extra': detalles_extra,
        'puede_validar': es_admin(request),
    })


@admin_required  # 'empleado' no puede eliminar nada salvo clientes sin cotizaciones (ver usuario_delete)
def cotizacion_delete(request, pk):
    cotizacion = get_object_or_404(Cotizacion, pk=pk)

    # Una cotización en estado "Pagado" no se puede eliminar, ni
    # siquiera un admin: a esta altura es un registro de que el cliente
    # ya pagó, y borrarla perdería ese rastro. Si "Pagado" se marcó por
    # error, la solución es entrar a "Validar" y cambiarle el estado
    # (eso sigue permitido) antes de intentar eliminarla.
    #
    # Para desactivar esta restricción manualmente, borra o comenta las
    # siguientes 3 líneas (el `if` de abajo hasta el `return` incluido).
    if cotizacion.estado == Cotizacion.ESTADO_PAGADO:
        messages.error(request, 'No se puede eliminar una cotización con estado "Pagado". Si fue un error, cámbiale primero el estado desde "Validar".')
        return redirect('panel_admin:cotizaciones_list')

    if request.method == 'POST':
        cotizacion.delete()
        messages.success(request, 'Cotización eliminada correctamente.')
        return redirect('panel_admin:cotizaciones_list')
    return render(request, 'panel_admin/confirmar_eliminar.html', {
        'objeto': cotizacion, 'titulo': 'cotización', 'cancelar_url': 'panel_admin:cotizaciones_list',
    })


# ───────────────────────────── Historial + PDF ─────────────────────────────
#
# El historial se arma sobre DetalleCotizacion (no sobre Cotizacion)
# porque es ahí donde vive `fecha_cotizacion` (auto_now_add): la fecha en
# que la solicitud fue REALIZADA por el cliente. `fecha_evento` (en
# Cotizacion) es la fecha del evento en sí, que puede ser meses después;
# para un "historial de cotizaciones hechas" lo que importa es cuándo se
# generó la solicitud, no cuándo será la fiesta.

# Opciones del filtro de fechas (valor en la URL, texto que ve el usuario).
# "Último año" y "último mes" cuentan hacia atrás desde hoy (365 y 30 días).
FILTROS_FECHA = [
    ('siempre', 'Siempre'),
    ('anio', 'Último año'),
    ('mes', 'Último mes'),
    ('rango', 'Rango de fechas'),
]
DIAS_POR_FILTRO = {'anio': 365, 'mes': 30}


def _leer_fecha(texto):
    try:
        return datetime.strptime(texto, '%Y-%m-%d').date()
    except (TypeError, ValueError):
        return None


def _filtrar_cotizaciones(request, queryset, campo_fecha, campo_estado):
    """
    Filtra por estado y por fecha de la cotización (cuándo la hizo el
    cliente). Lo usan el historial, su PDF y el listado de cotizaciones;
    como cada uno parte de un modelo distinto, se le indica en qué campo
    está la fecha y en cuál el estado. Devuelve (queryset, contexto).
    """
    filtro = request.GET.get('filtro', 'siempre')
    estado = request.GET.get('estado', '')
    desde_txt = request.GET.get('desde', '')
    hasta_txt = request.GET.get('hasta', '')

    if filtro in DIAS_POR_FILTRO:
        limite = timezone.now() - timedelta(days=DIAS_POR_FILTRO[filtro])
        queryset = queryset.filter(**{f'{campo_fecha}__gte': limite})
    elif filtro == 'rango':
        desde, hasta = _leer_fecha(desde_txt), _leer_fecha(hasta_txt)
        if (desde_txt and not desde) or (hasta_txt and not hasta):
            messages.error(request, 'Alguna de las fechas del rango no es válida.')
        if desde and hasta and desde > hasta:
            desde, hasta = hasta, desde
            desde_txt, hasta_txt = hasta_txt, desde_txt
        if desde:
            queryset = queryset.filter(**{f'{campo_fecha}__date__gte': desde})
        if hasta:
            queryset = queryset.filter(**{f'{campo_fecha}__date__lte': hasta})
    else:
        filtro = 'siempre'

    estados_validos = dict(Cotizacion.ESTADO_CHOICES)
    if estado in estados_validos:
        queryset = queryset.filter(**{campo_estado: estado})
    else:
        estado = ''

    # Mismos filtros en forma de querystring, para la paginación y el PDF.
    parametros = request.GET.copy()
    parametros.pop('page', None)

    contexto = {
        'filtro': filtro,
        'estado': estado,
        'desde': desde_txt,
        'hasta': hasta_txt,
        'filtros_fecha': FILTROS_FECHA,
        'estados': Cotizacion.ESTADO_CHOICES,
        'querystring': parametros.urlencode(),
    }
    return queryset, contexto


def _descripcion_filtro(contexto):
    """Texto legible del filtro aplicado, para el encabezado del PDF."""
    partes = [dict(FILTROS_FECHA).get(contexto['filtro'], 'Siempre')]
    if contexto['filtro'] == 'rango':
        partes[0] += f" ({contexto['desde'] or '…'} a {contexto['hasta'] or '…'})"
    if contexto['estado']:
        partes.append(f"estado {dict(Cotizacion.ESTADO_CHOICES)[contexto['estado']]}")
    return ', '.join(partes)


def _filtrar_historial(request):
    detalles = DetalleCotizacion.objects.select_related('cotizacion', 'cotizacion__cliente')
    detalles, contexto = _filtrar_cotizaciones(request, detalles, 'fecha_cotizacion', 'cotizacion__estado')
    return detalles.order_by('-fecha_cotizacion'), contexto


@staff_required
def historial_list(request):
    detalles, contexto_filtro = _filtrar_historial(request)

    totales = detalles.aggregate(
        cantidad=Count('id_detalle'),
        suma_cotizado=Sum('precio_cotizado'),
        suma_presupuesto=Sum('presupuesto'),
    )

    paginator = Paginator(detalles, 15)
    numero_pagina = request.GET.get('page')
    pagina = paginator.get_page(numero_pagina)

    contexto = {
        'pagina': pagina,
        'totales': totales,
        **contexto_filtro,
    }
    return render(request, 'panel_admin/historial.html', contexto)


@staff_required
def historial_pdf(request):
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter, landscape
    from reportlab.lib.units import cm
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet

    detalles, contexto_filtro = _filtrar_historial(request)
    totales = detalles.aggregate(
        cantidad=Count('id_detalle'),
        suma_cotizado=Sum('precio_cotizado'),
        suma_presupuesto=Sum('presupuesto'),
    )

    descripcion_filtro = _descripcion_filtro(contexto_filtro)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="historial_cotizaciones.pdf"'

    doc = SimpleDocTemplate(response, pagesize=landscape(letter),
                             topMargin=1.5 * cm, bottomMargin=1.5 * cm)
    estilos = getSampleStyleSheet()
    elementos = [
        Paragraph('Premium Eventos JM — Historial de cotizaciones', estilos['Title']),
        Paragraph(f'Filtro aplicado: {descripcion_filtro}', estilos['Normal']),
        Paragraph(f"Generado: {timezone.localtime().strftime('%Y-%m-%d %H:%M')}", estilos['Normal']),
        Spacer(1, 0.5 * cm),
    ]

    encabezados = ['Código', 'Cliente', 'Evento', 'Fecha evento', 'Invitados',
                    'Presupuesto', 'Precio cotizado', 'Estado', 'Fecha cotización']
    filas = [encabezados]
    for detalle in detalles:
        cot = detalle.cotizacion
        filas.append([
            cot.codigo_seguimiento,
            cot.nombre_cliente,
            detalle.evento,
            cot.fecha_evento.strftime('%Y-%m-%d'),
            formatear_miles(cot.cantidad_invitados),
            f'${formatear_miles(detalle.presupuesto)}',
            f'${formatear_miles(detalle.precio_cotizado)}',
            cot.get_estado_display(),
            timezone.localtime(detalle.fecha_cotizacion).strftime('%Y-%m-%d %H:%M'),
        ])

    tabla = Table(filas, repeatRows=1)
    tabla.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#c17b3c')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#fdf6ee')]),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    elementos.append(tabla)

    elementos.append(Spacer(1, 0.5 * cm))
    resumen = (
        f"Total de cotizaciones: {formatear_miles(totales['cantidad'] or 0)}    |    "
        f"Suma presupuestos: ${formatear_miles(totales['suma_presupuesto'] or 0)}    |    "
        f"Suma cotizado: ${formatear_miles(totales['suma_cotizado'] or 0)}"
    )
    elementos.append(Paragraph(resumen, estilos['Heading4']))

    doc.build(elementos)
    return response
