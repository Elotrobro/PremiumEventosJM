from django.shortcuts import render, redirect
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

from .models import Usuario, Cliente, Cotizacion, DetalleCotizacion, ContactoSimple,Testimonio
from .forms import TestimonioForm
from .n8n import enviar_a_n8n
from .precios import calcular_total_cotizacion  # la tabla de precios se edita en el panel
from . import limpieza, verificacion
from .validaciones import (
    errores_contrasena, errores_nombre, errores_telefono, limpiar_nombre, limpiar_telefono,
)

logger = logging.getLogger(__name__)


def login_view(request):
    """
    Autentica al usuario contra la tabla `usuario` de la base de datos.
    Si las credenciales son válidas, guarda los datos básicos del usuario
    en la sesión (id, nombre y rol) para que el resto del sitio pueda
    saber que hay una sesión activa (ver base.html).

    El formulario de inicio de sesión ya NO es una página aparte: vive
    como una ventana modal dentro de base.html (visible en cualquier
    página). Por eso esta vista nunca hace `render(...)`: siempre
    redirige a 'inicio'. Cuando hace falta que la modal se vuelva a
    abrir sola (por ejemplo, si las credenciales fueron incorrectas, o
    si alguien llega aquí sin haber iniciado sesión), se agrega
    `?login=1` a la URL de redirección; base.html lee ese parámetro y
    abre la modal automáticamente al cargar la página (ver login-modal.js).
    """
    url_inicio_con_modal = f"{reverse('inicio')}?login=1"

    # Si ya hay una sesión activa, no tiene sentido volver a mostrar el login
    if request.session.get('usuario_id'):
        return redirect('inicio')

    # GET (alguien entra a /login/ directamente, o algún flujo del sitio
    # redirige aquí porque exige sesión, ver modal.js/catalogo.js):
    # se manda a inicio con la modal abierta.
    if request.method != 'POST':
        return redirect(url_inicio_con_modal)

    # Elimina (máximo una vez al día) las cuentas de cliente que llevan 60
    # días sin cotizar; así una cuenta vencida ya no puede iniciar sesión.
    limpieza.ejecutar_si_toca()

    # .strip() quita espacios accidentales; .lower() normaliza el correo
    # porque la búsqueda de abajo también es insensible a mayúsculas.
    correo = request.POST.get('correo_electronico', '').strip().lower()
    contrasena = request.POST.get('contrasena', '')

    # Validación básica: ambos campos son obligatorios en el HTML,
    # pero se revisa también en servidor por si llega una petición
    # manipulada (sin pasar por el formulario).
    if not correo or not contrasena:
        messages.error(request, 'Por favor completa todos los campos.', extra_tags='login-error')
        request.session['login_correo_prefill'] = correo
        return redirect(url_inicio_con_modal)

    # Se busca el usuario por correo (case-insensitive con __iexact).
    # Si no existe, `usuario` queda en None y más abajo el login falla
    # igual que si la contraseña fuera incorrecta (no se revela cuál
    # de los dos datos fue el que falló).
    try:
        usuario = Usuario.objects.get(correo_electronico__iexact=correo)
    except Usuario.DoesNotExist:
        usuario = None

    credenciales_validas = False
    if usuario is not None:
        # Todas las contraseñas se guardan hasheadas (ver registro_view,
        # panel_admin/forms.py, admin.py y el comando crear_admin), así que
        # check_password es la única comparación válida: rehashea lo que
        # escribió la persona con la sal guardada y compara los resultados.
        credenciales_validas = check_password(contrasena, usuario.contrasena)

    if credenciales_validas:
        # Se registra la hora del último acceso exitoso. `update_fields`
        # hace que el UPDATE solo toque esa columna (más eficiente que
        # guardar todo el registro).
        usuario.ultimo_acceso = timezone.now()
        usuario.save(update_fields=['ultimo_acceso'])

        # Estos 3 valores en `request.session` son el "estado de sesión"
        # que usa el resto del sitio: base.html los lee para mostrar el
        # chip de usuario, y modal.js/catalogo.js los leen indirectamente
        # a través del atributo data-logged-in en <body>.
        request.session['usuario_id'] = usuario.id_usuario
        request.session['usuario_nombre'] = usuario.nombre_completo
        request.session['usuario_rol'] = usuario.rol
        request.session.pop('login_correo_prefill', None)

        messages.success(request, f'¡Bienvenido, {usuario.nombre_completo}!')
        return redirect('inicio')

    # Credenciales inválidas (usuario no existe o contraseña incorrecta):
    # se reenvía el correo ya escrito para que el usuario no tenga que
    # volver a teclearlo (ver value="{{ request.session.login_correo_prefill }}" en base.html).
    messages.error(request, 'Correo electrónico o contraseña incorrectos.', extra_tags='login-error')
    request.session['login_correo_prefill'] = correo
    return redirect(url_inicio_con_modal)


def registro_view(request):
    """
    Crea una cuenta nueva desde la pestaña "Crear cuenta" de la misma
    modal del login (ver base.html). Todas las cuentas que salen de aquí
    quedan con rol 'cliente': el rol 'admin' solo se asigna desde el
    panel de administrador o con el comando `manage.py crear_admin`, así
    que nadie puede darse permisos de administrador registrándose.

    Igual que login_view, esta vista nunca hace render(): siempre
    redirige a inicio, y agrega `?registro=1` cuando la modal debe
    reabrirse en la pestaña de registro para mostrar los errores.
    """
    url_con_modal = f"{reverse('inicio')}?registro=1"

    # Con una sesión activa no tiene sentido crear otra cuenta
    if request.session.get('usuario_id'):
        return redirect('inicio')

    if request.method != 'POST':
        return redirect(url_con_modal)

    nombre = limpiar_nombre(request.POST.get('nombre_completo', ''))
    correo = request.POST.get('correo_electronico', '').strip().lower()
    contrasena = request.POST.get('contrasena', '')
    confirmacion = request.POST.get('contrasena_confirmacion', '')

    # Se guardan los datos ya escritos (menos las contraseñas) para
    # devolverlos al formulario si algo falla y no tener que retecleárlos.
    request.session['registro_prefill'] = {'nombre': nombre, 'correo': correo}

    errores = []

    if not nombre or not correo or not contrasena:
        errores.append('Completa todos los campos obligatorios.')
    elif nombre:
        errores.extend(errores_nombre(nombre, 'el nombre completo'))

    if correo:
        try:
            validate_email(correo)
        except ValidationError:
            errores.append('El correo electrónico no tiene un formato válido.')
        else:
            # Validación clave: el correo es el identificador con el que se
            # inicia sesión, así que no puede estar en dos cuentas. Se
            # compara sin distinguir mayúsculas para que "Ana@x.com" y
            # "ana@x.com" cuenten como el mismo correo.
            if Usuario.objects.filter(correo_electronico__iexact=correo).exists():
                errores.append('Ya existe una cuenta registrada con ese correo electrónico.')

    if contrasena:
        errores.extend(errores_contrasena(contrasena))  # reglas en validaciones.py
        if contrasena != confirmacion:
            errores.append('Las contraseñas no coinciden.')

    if errores:
        for error in errores:
            messages.error(request, error, extra_tags='registro-error')
        return redirect(url_con_modal)

    # La contraseña se guarda siempre hasheada, igual que en el admin y en
    # el comando crear_admin (nunca en texto plano).
    # La cuenta todavía no se crea: primero se envía un código al correo y
    # se crea cuando la persona lo confirma (ver verificacion.py).
    verificacion.iniciar_verificacion(request, nombre, correo, make_password(contrasena))
    return redirect('verificar_correo')


def logout_view(request):
    """Cierra la sesión del usuario y lo regresa al inicio."""
    # flush() borra TODOS los datos de la sesión (no solo usuario_id),
    # y genera una nueva session key por seguridad.
    request.session.flush()
    messages.success(request, 'Has cerrado sesión correctamente.')
    return redirect('inicio')


def _notificar_cotizacion(request, cotizacion, detalle, servicios, sugerencias_sede, observaciones):
    """
    Le pasa a n8n los datos de la cotización recién creada; n8n le envía
    el detalle a la administradora y la confirmación al cliente. Si no hay
    URL configurada no se hace nada, y si n8n falla solo se deja el error
    en la consola: la cotización ya quedó guardada y el cliente no debe
    ver un error por culpa del correo.
    """
    if not settings.N8N_WEBHOOK_COTIZACION_URL:
        return

    def si_no(valor):
        return 'Sí' if valor == 'si' else 'No' if valor == 'no' else 'Sin especificar'

    servicios_legibles = [s.replace('_', ' ').capitalize() for s in servicios]
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
        'servicios_texto': ', '.join(servicios_legibles) or 'Ninguno seleccionado',
        'presupuesto': f'${formatear_miles(detalle.presupuesto)}',
        'precio_estimado': f'${formatear_miles(detalle.precio_cotizado)}',
        'observaciones': observaciones or 'Sin observaciones',
        'enlace_panel': request.build_absolute_uri(
            reverse('panel_admin:cotizacion_edit', args=[cotizacion.pk])
        ),
    }
    try:
        enviar_a_n8n(settings.N8N_WEBHOOK_COTIZACION_URL, datos)
    except Exception:
        logger.exception('n8n no respondió; no se enviaron los correos de la cotización %s.',
                         cotizacion.codigo_seguimiento)


def cotizacion_view(request):
    """
    Procesa el formulario de la modal "Solicita tu cotización" (en
    inicio.html) y lo guarda en las tablas Cliente / Cotizacion /
    DetalleCotizacion. Requiere sesión activa: el botón "Cotizar" ya
    valida esto en el navegador (modal.js), pero aquí se vuelve a
    comprobar en el servidor porque nunca hay que confiar solo en el
    frontend.
    """
    # Guarda de seguridad #1: sin sesión activa no se procesa nada.
    usuario_id = request.session.get('usuario_id')
    if not usuario_id:
        messages.error(request, 'Debes iniciar sesión para realizar una cotización.')
        return redirect('login')

    # Guarda de seguridad #2: esta vista solo procesa envíos por POST
    # (el formulario en inicio.html es method="post"); cualquier otro
    # método (ej. entrar directo por URL con GET) se redirige sin hacer nada.
    if request.method != 'POST':
        return redirect('inicio')

    # ---- Datos del formulario ----
    # Se leen todos los campos del <form id="formCotizacion"> de inicio.html.
    # request.POST.getlist() se usa para 'servicios' porque son varios
    # checkboxes con el mismo `name="servicios"`.
    nombre = limpiar_nombre(request.POST.get('nombre', ''))
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

    # ---- Validación mínima de campos obligatorios ----
    # No se usa un Django Form/ModelForm; la validación se hace a mano
    # revisando que ninguno de estos campos haya llegado vacío.
    campos_obligatorios = {
        'nombre': nombre, 'telefono': telefono, 'correo': correo,
        'tipo_evento': tipo_evento, 'fecha_evento': fecha_evento,
        'hora_evento': hora_evento, 'invitados': invitados, 'salon': salon,
    }
    faltantes = [campo for campo, valor in campos_obligatorios.items() if not valor]
    if faltantes:
        messages.error(request, 'Faltan campos obligatorios en el formulario de cotización.')
        return redirect('inicio')

    errores = errores_nombre(nombre, 'el nombre completo') + errores_telefono(telefono)
    telefono = limpiar_telefono(telefono)
    try:
        validate_email(correo)
    except ValidationError:
        errores.append('El correo electrónico no tiene un formato válido.')
    if errores:
        for error in errores:
            messages.error(request, error)
        return redirect('inicio')

    # El input type="date"/"time" del HTML siempre manda estos formatos
    # exactos (YYYY-MM-DD y HH:MM), pero se valida igual por si el dato
    # llegara manipulado o desde otro cliente distinto al navegador.
    try:
        fecha_evento_dt = datetime.strptime(fecha_evento, '%Y-%m-%d').date()
        hora_inicio_dt = datetime.strptime(hora_evento, '%H:%M').time()
    except ValueError:
        messages.error(request, 'La fecha u hora del evento no tienen un formato válido.')
        return redirect('inicio')

    # La hora de finalización no la pide el formulario; se estima en 4
    # horas de duración (valor típico de un evento social) y queda
    # registrada como estimación en el campo "detalles".
    hora_fin_dt = (datetime.combine(fecha_evento_dt, hora_inicio_dt) + timedelta(hours=4)).time()

    try:
        cantidad_invitados = int(invitados)
    except ValueError:
        messages.error(request, 'La cantidad de invitados debe ser un número.')
        return redirect('inicio')

    try:
        presupuesto_dec = Decimal(presupuesto) if presupuesto else Decimal('0')
    except InvalidOperation:
        presupuesto_dec = Decimal('0')

    usuario = Usuario.objects.get(pk=usuario_id)

    # ---- Cliente: se reutiliza si ya existe uno ligado a este usuario ----
    cliente, _creado = Cliente.objects.get_or_create(
        usuario=usuario,
        defaults={
            'nombre_completo': nombre,
            'correo_electronico': correo,
            'telefono_whatsapp': telefono,
        },
    )
    # Se mantienen los datos de contacto actualizados con lo último que envió
    cliente.nombre_completo = nombre
    cliente.correo_electronico = correo
    cliente.telefono_whatsapp = telefono
    cliente.save()

        # ---- Cotizacion ----
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

    # ---- DetalleCotizacion ----

    # Calcula el precio base + los servicios seleccionados
    precio_estimado = calcular_total_cotizacion(
        cantidad_invitados,
        servicios
    )

    detalles_extra = {
        'servicios_solicitados': servicios,
        'desea_sugerencias_sede': sugerencias_sede,
        'observaciones': mensaje,
        'hora_fin_estimada':
            'Calculada automáticamente (+4h desde la hora de inicio)',
    }

    detalle = DetalleCotizacion.objects.create(
        cotizacion=cotizacion,
        cantidad_personas_aplica=cantidad_invitados,
        salon=(salon == 'si'),
        detalles=json.dumps(
            detalles_extra,
            ensure_ascii=False
        ),
        evento=tipo_evento,
        presupuesto=presupuesto_dec,
        precio_cotizado=precio_estimado,
    )

    # ---- Correos (administradora + cliente) a través de n8n ----
    _notificar_cotizacion(
        request,
        cotizacion,
        detalle,
        servicios,
        sugerencias_sede,
        mensaje
    )

    messages.success(
        request,
        f'¡Gracias, {nombre}! Tu solicitud de cotización fue registrada con un estimado de '
        f'${formatear_miles(precio_estimado)}. '
        'Esta es una cotización aproximada; te contactaremos pronto para confirmar los detalles. '
        f'Tu código de seguimiento es {cotizacion.codigo_seguimiento} — consérvalo para futuras consultas.'
    )

    return redirect('inicio')


def guardar_contacto(request):
    """
    Procesa el formulario público de contacto.html y lo guarda en
    ContactoSimple. No requiere sesión iniciada (a diferencia de la
    cotización): cualquier visitante puede dejar sus datos de contacto.
    """
    if request.method != 'POST':
        return redirect('contacto')

    nombre = limpiar_nombre(request.POST.get('nombre', ''))
    apellidos = limpiar_nombre(request.POST.get('apellidos', ''))
    email = request.POST.get('email', '').strip()
    telefono = request.POST.get('telefono', '').strip()
    mensaje = request.POST.get('mensaje', '').strip()

    if not nombre or not apellidos or not email or not mensaje:
        messages.error(request, 'Por favor completa los campos obligatorios del formulario.')
        return redirect('contacto')

    errores = errores_nombre(nombre, 'el nombre') + errores_nombre(apellidos, 'los apellidos')
    if telefono:
        errores += errores_telefono(telefono)
        telefono = limpiar_telefono(telefono)
    try:
        validate_email(email)
    except ValidationError:
        errores.append('El correo electrónico no tiene un formato válido.')
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

    messages.success(request, f'¡Gracias, {nombre}! Hemos recibido tu mensaje y te contactaremos pronto.')
    return redirect('contacto')


# Mostrar testimonios
def testimonios(request):

    testimonios_publicados = Testimonio.objects.filter(
        aprobado=True
    ).select_related("usuario")

    usuario_id = request.session.get("usuario_id")

    if request.method == "POST":

        if not usuario_id:
            return redirect("/?login=1")

        form = TestimonioForm(request.POST)

        if form.is_valid():

            testimonio = form.save(commit=False)
            testimonio.usuario_id = usuario_id
            testimonio.aprobado = False

            testimonio.save()

            messages.success(request,"¡Gracias por compartir tu experiencia! Tu opinión fue enviada y será revisada antes de publicarse.");

            return redirect("testimonios")

    else:
        form = TestimonioForm()

    return render(
        request,
        "testimonios.html",
        {
            "testimonios": testimonios_publicados,
            "form": form,
            "usuario_logueado": bool(usuario_id),
        }
    )