from datetime import datetime

from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Sum, Count
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone

from Bd_PremiumEventos.models import (
    Usuario, ContactoSimple, ItemDecoracion, Cotizacion, DetalleCotizacion,
)
from .decorators import admin_required
from .forms import UsuarioAdminForm, ItemDecoracionForm, CotizacionEstadoForm

# ═══════════════════════════════════════════════════════════════════════
# Panel de administrador a medida (no es el admin genérico de Django).
#
# Todas las vistas de este módulo están protegidas con @admin_required
# (solo entra quien tenga request.session['usuario_rol'] == 'admin') y
# usan plantillas propias que extienden panel_admin/base_admin.html para
# mantener el estilo del sitio.
# ═══════════════════════════════════════════════════════════════════════


@admin_required
def dashboard(request):
    contexto = {
        'total_usuarios': Usuario.objects.count(),
        'total_cotizaciones': Cotizacion.objects.count(),
        'cotizaciones_pendientes': Cotizacion.objects.filter(estado=Cotizacion.ESTADO_PENDIENTE).count(),
        'total_mensajes': ContactoSimple.objects.count(),
        'total_items': ItemDecoracion.objects.count(),
    }
    return render(request, 'panel_admin/dashboard.html', contexto)


# ───────────────────────────── Usuarios ─────────────────────────────

@admin_required
def usuarios_list(request):
    usuarios = Usuario.objects.all().order_by('nombre_completo')
    return render(request, 'panel_admin/usuarios_list.html', {'usuarios': usuarios})


@admin_required
def usuario_create(request):
    if request.method == 'POST':
        form = UsuarioAdminForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Usuario creado correctamente.')
            return redirect('panel_admin:usuarios_list')
    else:
        form = UsuarioAdminForm()
    return render(request, 'panel_admin/usuario_form.html', {'form': form, 'modo': 'crear'})


@admin_required
def usuario_edit(request, pk):
    usuario = get_object_or_404(Usuario, pk=pk)
    if request.method == 'POST':
        form = UsuarioAdminForm(request.POST, instance=usuario)
        if form.is_valid():
            form.save()
            messages.success(request, 'Usuario actualizado correctamente.')
            return redirect('panel_admin:usuarios_list')
    else:
        form = UsuarioAdminForm(instance=usuario)
    return render(request, 'panel_admin/usuario_form.html', {'form': form, 'modo': 'editar', 'usuario': usuario})


@admin_required
def usuario_delete(request, pk):
    usuario = get_object_or_404(Usuario, pk=pk)
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

@admin_required
def catalogo_list(request):
    items = ItemDecoracion.objects.all().order_by('nombre')
    return render(request, 'panel_admin/catalogo_list.html', {'items': items})


@admin_required
def catalogo_create(request):
    if request.method == 'POST':
        form = ItemDecoracionForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Ítem de decoración creado correctamente.')
            return redirect('panel_admin:catalogo_list')
    else:
        form = ItemDecoracionForm()
    return render(request, 'panel_admin/catalogo_form.html', {'form': form, 'modo': 'crear'})


@admin_required
def catalogo_edit(request, pk):
    item = get_object_or_404(ItemDecoracion, pk=pk)
    if request.method == 'POST':
        form = ItemDecoracionForm(request.POST, instance=item)
        if form.is_valid():
            form.save()
            messages.success(request, 'Ítem de decoración actualizado correctamente.')
            return redirect('panel_admin:catalogo_list')
    else:
        form = ItemDecoracionForm(instance=item)
    return render(request, 'panel_admin/catalogo_form.html', {'form': form, 'modo': 'editar', 'item': item})


@admin_required
def catalogo_delete(request, pk):
    item = get_object_or_404(ItemDecoracion, pk=pk)
    if request.method == 'POST':
        item.delete()
        messages.success(request, 'Ítem de decoración eliminado correctamente.')
        return redirect('panel_admin:catalogo_list')
    return render(request, 'panel_admin/confirmar_eliminar.html', {
        'objeto': item, 'titulo': 'ítem de decoración', 'cancelar_url': 'panel_admin:catalogo_list',
    })


# ─────────────────── Mensajes de contacto (ContactoSimple) ───────────────────

@admin_required
def mensajes_list(request):
    mensajes = ContactoSimple.objects.all().order_by('-fecha_contacto')
    return render(request, 'panel_admin/mensajes_list.html', {'mensajes': mensajes})


@admin_required
def mensaje_delete(request, pk):
    mensaje = get_object_or_404(ContactoSimple, pk=pk)
    if request.method == 'POST':
        mensaje.delete()
        messages.success(request, 'Mensaje eliminado correctamente.')
        return redirect('panel_admin:mensajes_list')
    return render(request, 'panel_admin/confirmar_eliminar.html', {
        'objeto': mensaje, 'titulo': 'mensaje de contacto', 'cancelar_url': 'panel_admin:mensajes_list',
    })


# ───────────────────────────── Cotizaciones ─────────────────────────────

@admin_required
def cotizaciones_list(request):
    cotizaciones = Cotizacion.objects.select_related('cliente').order_by('-id_cotizacion')
    return render(request, 'panel_admin/cotizaciones_list.html', {'cotizaciones': cotizaciones})


@admin_required
def cotizacion_edit(request, pk):
    cotizacion = get_object_or_404(Cotizacion, pk=pk)
    if request.method == 'POST':
        form = CotizacionEstadoForm(request.POST, instance=cotizacion)
        if form.is_valid():
            form.save()
            messages.success(request, 'Cotización actualizada correctamente.')
            return redirect('panel_admin:cotizaciones_list')
    else:
        form = CotizacionEstadoForm(instance=cotizacion)
    return render(request, 'panel_admin/cotizacion_form.html', {'form': form, 'cotizacion': cotizacion})


@admin_required
def cotizacion_delete(request, pk):
    cotizacion = get_object_or_404(Cotizacion, pk=pk)
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

def _filtrar_historial(request):
    """
    Aplica el filtro de fecha elegido y devuelve (queryset, contexto_filtro).
    Filtros soportados: 'siempre' (todo), 'anio' (año en curso) y
    'fecha' (una fecha exacta, elegida con un <input type="date">).
    """
    filtro = request.GET.get('filtro', 'siempre')
    fecha_str = request.GET.get('fecha', '')

    detalles = DetalleCotizacion.objects.select_related('cotizacion', 'cotizacion__cliente')

    if filtro == 'anio':
        anio_actual = timezone.localdate().year
        detalles = detalles.filter(fecha_cotizacion__year=anio_actual)
    elif filtro == 'fecha' and fecha_str:
        try:
            fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
            detalles = detalles.filter(fecha_cotizacion__date=fecha)
        except ValueError:
            messages.error(request, 'La fecha ingresada no es válida.')
            filtro = 'siempre'
    else:
        filtro = 'siempre'

    detalles = detalles.order_by('-fecha_cotizacion')

    contexto_filtro = {'filtro': filtro, 'fecha': fecha_str}
    return detalles, contexto_filtro


@admin_required
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


@admin_required
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

    etiquetas_filtro = {'siempre': 'Siempre', 'anio': 'Este año', 'fecha': 'Fecha específica'}
    descripcion_filtro = etiquetas_filtro.get(contexto_filtro['filtro'], 'Siempre')
    if contexto_filtro['filtro'] == 'fecha' and contexto_filtro['fecha']:
        descripcion_filtro += f" ({contexto_filtro['fecha']})"

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

    encabezados = ['#', 'Cliente', 'Evento', 'Fecha evento', 'Invitados',
                    'Presupuesto', 'Precio cotizado', 'Estado', 'Fecha cotización']
    filas = [encabezados]
    for detalle in detalles:
        cot = detalle.cotizacion
        filas.append([
            str(cot.id_cotizacion),
            cot.nombre_cliente,
            detalle.evento,
            cot.fecha_evento.strftime('%Y-%m-%d'),
            str(cot.cantidad_invitados),
            f'${detalle.presupuesto:,.0f}',
            f'${detalle.precio_cotizado:,.0f}',
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
        f"Total de cotizaciones: {totales['cantidad'] or 0}    |    "
        f"Suma presupuestos: ${(totales['suma_presupuesto'] or 0):,.0f}    |    "
        f"Suma cotizado: ${(totales['suma_cotizado'] or 0):,.0f}"
    )
    elementos.append(Paragraph(resumen, estilos['Heading4']))

    doc.build(elementos)
    return response
