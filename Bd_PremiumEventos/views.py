
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.urls import reverse
from django.contrib import messages
from django.contrib.auth.hashers import check_password, make_password
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.utils import timezone
from django.conf import settings
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation
import json
import logging

from panel_admin.utils import formatear_miles

from .models import (
    Usuario,
    Cliente,
    Cotizacion,
    DetalleCotizacion,
    ContactoSimple,
    Testimonio,
)
from .forms import TestimonioForm
from .n8n import enviar_a_n8n
from .precios import calcular_total_cotizacion
from . import limpieza, verificacion
from .validaciones import (
    errores_contrasena,
    errores_nombre,
    errores_telefono,
    limpiar_nombre,
    limpiar_telefono,
)

logger = logging.getLogger(__name__)


def login_view(request):
    """
    Autentica al usuario y guarda los datos básicos en la sesión.
    El formulario de inicio de sesión vive en una ventana modal
    dentro de base.html, por lo que esta vista redirige a inicio.
    """
    url_inicio_con_modal = f"{reverse('inicio')}?login=1"

    if request.session.get('usuario_id'):
        return redirect('inicio')

    if request.method != 'POST':
        return redirect(url_inicio_con_modal)

    limpieza.ejecutar_si_toca()

    correo = request.POST.get('correo_electronico', '').strip().lower()
    contrasena = request.POST.get('contrasena', '')

    if not correo or not contrasena:
        messages.error(
            request,
            'Por favor completa todos los campos.',
            extra_tags='login-error',
        )
        request.session['login_correo_prefill'] = correo
        return redirect(url_inicio_con_modal)

    try:
        usuario = Usuario.objects.get(correo_electronico__iexact=correo)
    except Usuario.DoesNotExist:
        usuario = None

    credenciales_validas = False

    if usuario is not None:
        credenciales_validas = check_password(
            contrasena,
            usuario.contrasena,
        )

    if credenciales_validas:
        usuario.ultimo_acceso = timezone.now()
        usuario.save(update_fields=['ultimo_acceso'])

        request.session['usuario_id'] = usuario.id_usuario
        request.session['usuario_nombre'] = usuario.nombre_completo
        request.session['usuario_rol'] = usuario.rol
        request.session.pop('login_correo_prefill', None)

        messages.success(
            request,
            f'¡Bienvenido, {usuario.nombre_completo}!',
        )
        return redirect('inicio')

    messages.error(
        request,
        'Correo electrónico o contraseña incorrectos.',
        extra_tags='login-error',
    )
    request.session['login_correo_prefill'] = correo

    return redirect(url_inicio_con_modal)


def registro_view(request):
    """
    Registra una cuenta nueva desde la ventana modal.
    La cuenta se crea cuando se confirma el código enviado al correo.
    """
    url_con_modal = f"{reverse('inicio')}?registro=1"

    if request.session.get('usuario_id'):
        return redirect('inicio')

    if request.method != 'POST':
        return redirect(url_con_modal)

    nombre = limpiar_nombre(
        request.POST.get('nombre_completo', '')
    )
    correo = request.POST.get(
        'correo_electronico',
        '',
    ).strip().lower()
    contrasena = request.POST.get('contrasena', '')
    confirmacion = request.POST.get(
        'contrasena_confirmacion',
        '',
    )

    request.session['registro_prefill'] = {
        'nombre': nombre,
        'correo': correo,
    }

    errores = []

    if not nombre or not correo or not contrasena:
        errores.append(
            'Completa todos los campos obligatorios.'
        )
    elif nombre:
        errores.extend(
            errores_nombre(nombre, 'el nombre completo')
        )

    if correo:
        try:
            validate_email(correo)
        except ValidationError:
            errores.append(
                'El correo electrónico no tiene un formato válido.'
            )
        else:
            if Usuario.objects.filter(
                correo_electronico__iexact=correo
            ).exists():
                errores.append(
                    'Ya existe una cuenta registrada con ese correo electrónico.'
                )

    if contrasena:
        errores.extend(errores_contrasena(contrasena))

        if contrasena != confirmacion:
            errores.append('Las contraseñas no coinciden.')

    if errores:
        for error in errores:
            messages.error(
                request,
                error,
                extra_tags='registro-error',
            )

        return redirect(url_con_modal)

    verificacion.iniciar_verificacion(
        request,
        nombre,
        correo,
        make_password(contrasena),
    )

    return redirect('verificar_correo')


def logout_view(request):
    """Cierra la sesión y redirige al usuario al inicio."""
    request.session.flush()

    messages.success(
        request,
        'Has cerrado sesión correctamente.',
    )

    return redirect('inicio')


def _notificar_cotizacion(
    request,
    cotizacion,
    detalle,
    servicios,
    sugerencias_sede,
    observaciones,
):
    """
    Envía los datos de la cotización a n8n.
    Si n8n falla, la cotización permanece guardada.
    """
    if not settings.N8N_WEBHOOK_COTIZACION_URL:
        return

    def si_no(valor):
        return (
            'Sí'
            if valor == 'si'
            else 'No'
            if valor == 'no'
            else 'Sin especificar'
        )

    servicios_legibles = [
        servicio.replace('_', ' ').capitalize()
        for servicio in servicios
    ]

    datos = {
        'codigo_seguimiento': cotizacion.codigo_seguimiento,
        'nombre': cotizacion.nombre_cliente,
        'correo': cotizacion.correo_cliente,
        'telefono': cotizacion.telefono_cliente,
        'tipo_evento': detalle.evento.capitalize(),
        'fecha_evento': cotizacion.fecha_evento.strftime('%d/%m/%Y'),
        'hora_inicio': cotizacion.hora_inicio.strftime('%H:%M'),
        'hora_fin': cotizacion.hora_fin.strftime('%H:%M'),
        'invitados': cotizacion.cantidad_invitados,
        'ubicacion': cotizacion.ubicacion,
        'tema_estilo': cotizacion.tema_estilo,
        'tiene_salon': 'Sí' if detalle.salon else 'No',
        'desea_sugerencias_sede': si_no(sugerencias_sede),
        'servicios': servicios_legibles,
        'servicios_texto': (
            ', '.join(servicios_legibles)
            or 'Ninguno seleccionado'
        ),
        'presupuesto': f'${formatear_miles(detalle.presupuesto)}',
        'precio_estimado': f'${formatear_miles(detalle.precio_cotizado)}',
        'observaciones': observaciones or 'Sin observaciones',
        'enlace_panel': request.build_absolute_uri(
            reverse(
                'panel_admin:cotizacion_edit',
                args=[cotizacion.pk],
            )
        ),
    }

    try:
        enviar_a_n8n(
            settings.N8N_WEBHOOK_COTIZACION_URL,
            datos,
        )
    except Exception:
        logger.exception(
            'n8n no respondió; no se enviaron los correos '
            'de la cotización %s.',
            cotizacion.codigo_seguimiento,
        )


def cotizacion_view(request):
    """
    Procesa el formulario de cotización y guarda los datos
    en Cliente, Cotizacion y DetalleCotizacion.
    Requiere una sesión activa.
    """
    usuario_id = request.session.get('usuario_id')

    if not usuario_id:
        messages.error(
            request,
            'Debes iniciar sesión para realizar una cotización.',
        )
        return redirect('login')

    if request.method != 'POST':
        return redirect('inicio')

    nombre = limpiar_nombre(
        request.POST.get('nombre', '')
    )
    telefono = request.POST.get('telefono', '').strip()
    correo = request.POST.get('correo', '').strip()
    tipo_evento = request.POST.get('tipo_evento', '').strip()
    fecha_evento = request.POST.get('fecha_evento', '').strip()
    hora_evento = request.POST.get('hora_evento', '').strip()
    invitados = request.POST.get('invitados', '').strip()
    lugar_evento = request.POST.get('lugar_evento', '').strip()
    salon = request.POST.get('salon', '')
    sugerencias_sede = request.POST.get('sugerencias_sede', '')
    servicios = request.POST.getlist('servicios')
    presupuesto = request.POST.get('presupuesto', '').strip()
    tema_evento = request.POST.get('tema_evento', '').strip()
    mensaje = request.POST.get('mensaje', '').strip()

    campos_obligatorios = {
        'nombre': nombre,
        'telefono': telefono,
        'correo': correo,
        'tipo_evento': tipo_evento,
        'fecha_evento': fecha_evento,
        'hora_evento': hora_evento,
        'invitados': invitados,
        'salon': salon,
    }

    faltantes = [
        campo
        for campo, valor in campos_obligatorios.items()
        if not valor
    ]

    if faltantes:
        messages.error(
            request,
            'Faltan campos obligatorios en el formulario de cotización.',
        )
        return redirect('inicio')

    errores = (
        errores_nombre(nombre, 'el nombre completo')
        + errores_telefono(telefono)
    )

    telefono = limpiar_telefono(telefono)

    try:
        validate_email(correo)
    except ValidationError:
        errores.append(
            'El correo electrónico no tiene un formato válido.'
        )

    if errores:
        for error in errores:
            messages.error(request, error)

        return redirect('inicio')

    try:
        fecha_evento_dt = datetime.strptime(
            fecha_evento,
            '%Y-%m-%d',
        ).date()

        hora_inicio_dt = datetime.strptime(
            hora_evento,
            '%H:%M',
        ).time()
    except ValueError:
        messages.error(
            request,
            'La fecha u hora del evento no tienen un formato válido.',
        )
        return redirect('inicio')

    hora_fin_dt = (
        datetime.combine(fecha_evento_dt, hora_inicio_dt)
        + timedelta(hours=4)
    ).time()

    try:
        cantidad_invitados = int(invitados)
    except ValueError:
        messages.error(
            request,
            'La cantidad de invitados debe ser un número.',
        )
        return redirect('inicio')

    try:
        presupuesto_dec = (
            Decimal(presupuesto)
            if presupuesto
            else Decimal('0')
        )
    except InvalidOperation:
        presupuesto_dec = Decimal('0')

    usuario = Usuario.objects.get(pk=usuario_id)

    cliente, _creado = Cliente.objects.get_or_create(
        usuario=usuario,
        defaults={
            'nombre_completo': nombre,
            'correo_electronico': correo,
            'telefono_whatsapp': telefono,
        },
    )

    cliente.nombre_completo = nombre
    cliente.correo_electronico = correo
    cliente.telefono_whatsapp = telefono
    cliente.save()

    cotizacion = Cotizacion.objects.create(
        cliente=cliente,
        nombre_cliente=nombre,
        correo_cliente=correo,
        telefono_cliente=telefono,
        fecha_evento=fecha_evento_dt,
        cantidad_invitados=cantidad_invitados,
        tema_estilo=tema_evento or 'Sin especificar',
        hora_inicio=hora_inicio_dt,
        hora_fin=hora_fin_dt,
        ubicacion=lugar_evento or 'Por definir',
    )

    precio_estimado = calcular_total_cotizacion(
        cantidad_invitados,
        servicios,
    )

    detalles_extra = {
        'servicios_solicitados': servicios,
        'desea_sugerencias_sede': sugerencias_sede,
        'observaciones': mensaje,
        'hora_fin_estimada': (
            'Calculada automáticamente (+4h desde la hora de inicio)'
        ),
    }

    detalle = DetalleCotizacion.objects.create(
        cotizacion=cotizacion,
        cantidad_personas_aplica=cantidad_invitados,
        salon=(salon == 'si'),
        detalles=json.dumps(
            detalles_extra,
            ensure_ascii=False,
        ),
        evento=tipo_evento,
        presupuesto=presupuesto_dec,
        precio_cotizado=precio_estimado,
    )

    _notificar_cotizacion(
        request,
        cotizacion,
        detalle,
        servicios,
        sugerencias_sede,
        mensaje,
    )

    messages.success(
        request,
        f'¡Gracias, {nombre}! Tu solicitud de cotización fue '
        f'registrada con un estimado de ${formatear_miles(precio_estimado)}. '
        'Esta es una cotización aproximada; te contactaremos pronto '
        'para confirmar los detalles. '
        f'Tu código de seguimiento es {cotizacion.codigo_seguimiento} '
        '— consérvalo para futuras consultas.',
    )

    return redirect('inicio')


def guardar_contacto(request):
    """
    Procesa el formulario público de contacto.html y guarda
    los datos en ContactoSimple.
    """
    if request.method != 'POST':
        return redirect('contacto')

    nombre = limpiar_nombre(
        request.POST.get('nombre', '')
    )
    apellidos = limpiar_nombre(
        request.POST.get('apellidos', '')
    )
    email = request.POST.get('email', '').strip()
    telefono = request.POST.get('telefono', '').strip()
    mensaje = request.POST.get('mensaje', '').strip()

    if not nombre or not apellidos or not email or not mensaje:
        messages.error(
            request,
            'Por favor completa los campos obligatorios del formulario.',
        )
        return redirect('contacto')

    errores = (
        errores_nombre(nombre, 'el nombre')
        + errores_nombre(apellidos, 'los apellidos')
    )

    if telefono:
        errores += errores_telefono(telefono)
        telefono = limpiar_telefono(telefono)

    try:
        validate_email(email)
    except ValidationError:
        errores.append(
            'El correo electrónico no tiene un formato válido.'
        )

    if errores:
        for error in errores:
            messages.error(request, error)

        return redirect('contacto')

    ContactoSimple.objects.create(
        nombre=nombre,
        apellidos=apellidos,
        email=email,
        telefono=telefono,
        mensaje=mensaje,
    )

    messages.success(
        request,
        f'¡Gracias, {nombre}! Hemos recibido tu mensaje '
        'y te contactaremos pronto.',
    )

    return redirect('contacto')


def testimonios(request):
    """
    Muestra cinco testimonios inicialmente y permite solicitar
    los siguientes grupos mediante peticiones AJAX.

    Conserva el envío de nuevos testimonios y requiere que estos
    sean aprobados antes de aparecer públicamente.
    """
    testimonios_publicados = (
        Testimonio.objects
        .filter(aprobado=True)
        .select_related('usuario')
    )

    usuario_id = request.session.get('usuario_id')

    if request.method == 'POST':
        if not usuario_id:
            return redirect('/?login=1')

        form = TestimonioForm(request.POST)

        if form.is_valid():
            testimonio = form.save(commit=False)
            testimonio.usuario_id = usuario_id
            testimonio.aprobado = False
            testimonio.save()

            messages.success(
                request,
                '¡Gracias por compartir tu experiencia! '
                'Tu opinión fue enviada y será revisada antes de publicarse.',
            )

            return redirect('testimonios')
    else:
        form = TestimonioForm()

    paginador = Paginator(testimonios_publicados, 5)
    total_testimonios = paginador.count

    # Solicitud AJAX para cargar los siguientes testimonios.
    if request.GET.get('fragment') == '1':
        try:
            numero_pagina = max(
                2,
                int(request.GET.get('page', '2')),
            )
        except (TypeError, ValueError):
            numero_pagina = 2

        pagina_obj = paginador.get_page(numero_pagina)

        items = [
            {
                'calificacion': testimonio.calificacion,
                'comentario': testimonio.comentario,
                'nombre': testimonio.usuario.nombre_completo,
            }
            for testimonio in pagina_obj.object_list
        ]

        return JsonResponse({
            'items': items,
            'next_page': numero_pagina + 1,
            'has_more': pagina_obj.has_next(),
            'total': total_testimonios,
        })

    # Primera carga: solo se muestran cinco testimonios.
    pagina_inicial = paginador.get_page(1)

    return render(
        request,
        'testimonios.html',
        {
            'testimonios': pagina_inicial.object_list,
            'form': form,
            'usuario_logueado': bool(usuario_id),
            'total_testimonios': total_testimonios,
            'tiene_mas': pagina_inicial.has_next(),
        },
    )
