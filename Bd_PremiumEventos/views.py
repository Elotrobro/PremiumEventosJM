from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib import messages
from django.contrib.auth.hashers import check_password, make_password, is_password_usable
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation
import json

from .models import Usuario, Cliente, Cotizacion, DetalleCotizacion, ContactoSimple


# ─────────────────────────────────────────────────────────────────────────
# Lógica de negocio: cálculo del precio estimado según cantidad de
# invitados. Es el mismo cálculo que hace modal.js en el navegador (para
# mostrarle un estimado en vivo al usuario); aquí se vuelve a calcular en
# el servidor porque el valor que se guarda en la base de datos nunca debe
# depender únicamente de lo que envía el navegador.
# ─────────────────────────────────────────────────────────────────────────
TABLA_PAQUETES = [
    (20, Decimal('1800000')),
    (30, Decimal('2600000')),
    (40, Decimal('3200000')),
    (50, Decimal('3900000')),
    (60, Decimal('4500000')),
    (70, Decimal('4900000')),
    (80, Decimal('5440000')),
    (90, Decimal('5850000')),
    (100, Decimal('5800000')),
]
TARIFA_INVITADO_ADICIONAL = Decimal('58000')  # eventos con más de 100 invitados


def calcular_precio_estimado(cantidad_invitados):
    """Replica en Python la tabla de paquetes usada en modal.js."""
    n = cantidad_invitados
    if not n or n <= 0:
        return Decimal('0')

    primero_inv, primero_precio = TABLA_PAQUETES[0]
    ultimo_inv, ultimo_precio = TABLA_PAQUETES[-1]

    if n <= primero_inv:
        return primero_precio

    if n >= ultimo_inv:
        extra = n - ultimo_inv
        return ultimo_precio + extra * TARIFA_INVITADO_ADICIONAL

    for (inv_inferior, precio_inferior), (inv_superior, precio_superior) in zip(TABLA_PAQUETES, TABLA_PAQUETES[1:]):
        if inv_inferior < n <= inv_superior:
            proporcion = Decimal(n - inv_inferior) / Decimal(inv_superior - inv_inferior)
            precio = precio_inferior + proporcion * (precio_superior - precio_inferior)
            return (precio / 1000).quantize(Decimal('1')) * 1000  # redondeo a miles

    return Decimal('0')


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
        # Los passwords se guardan hasheados (ver admin.py). Si por alguna
        # razón existiera un valor sin hashear en la BD, se compara en
        # texto plano como último recurso para no romper cuentas antiguas.
        if is_password_usable(usuario.contrasena):
            credenciales_validas = check_password(contrasena, usuario.contrasena)
        else:
            credenciales_validas = (contrasena == usuario.contrasena)

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

    nombre = request.POST.get('nombre_completo', '').strip()
    correo = request.POST.get('correo_electronico', '').strip().lower()
    contrasena = request.POST.get('contrasena', '')
    confirmacion = request.POST.get('contrasena_confirmacion', '')

    # Se guardan los datos ya escritos (menos las contraseñas) para
    # devolverlos al formulario si algo falla y no tener que retecleárlos.
    request.session['registro_prefill'] = {'nombre': nombre, 'correo': correo}

    errores = []

    if not nombre or not correo or not contrasena:
        errores.append('Completa todos los campos obligatorios.')

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
        if len(contrasena) < 8:
            errores.append('La contraseña debe tener al menos 8 caracteres.')
        elif contrasena.isdigit():
            errores.append('La contraseña no puede ser solo números.')
        if contrasena != confirmacion:
            errores.append('Las contraseñas no coinciden.')

    if errores:
        for error in errores:
            messages.error(request, error, extra_tags='registro-error')
        return redirect(url_con_modal)

    # La contraseña se guarda siempre hasheada, igual que en el admin y en
    # el comando crear_admin (nunca en texto plano).
    usuario = Usuario.objects.create(
        nombre_completo=nombre,
        correo_electronico=correo,
        contrasena=make_password(contrasena),
        rol='cliente',
        ultimo_acceso=timezone.now(),
    )

    # Se deja la sesión iniciada de una vez: quien se registra normalmente
    # viene de intentar cotizar, así que puede seguir sin volver a entrar.
    request.session['usuario_id'] = usuario.id_usuario
    request.session['usuario_nombre'] = usuario.nombre_completo
    request.session['usuario_rol'] = usuario.rol
    request.session.pop('registro_prefill', None)

    messages.success(request, f'¡Bienvenido, {usuario.nombre_completo}! Tu cuenta fue creada correctamente.')
    return redirect('inicio')


def logout_view(request):
    """Cierra la sesión del usuario y lo regresa al inicio."""
    # flush() borra TODOS los datos de la sesión (no solo usuario_id),
    # y genera una nueva session key por seguridad.
    request.session.flush()
    messages.success(request, 'Has cerrado sesión correctamente.')
    return redirect('inicio')


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
    nombre = request.POST.get('nombre', '').strip()
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
    precio_estimado = calcular_precio_estimado(cantidad_invitados)

    detalles_extra = {
        'servicios_solicitados': servicios,
        'desea_sugerencias_sede': sugerencias_sede,
        'observaciones': mensaje,
        'hora_fin_estimada': 'Calculada automáticamente (+4h desde la hora de inicio)',
    }
    DetalleCotizacion.objects.create(
        cotizacion=cotizacion,
        cantidad_personas_aplica=cantidad_invitados,
        salon=(salon == 'si'),
        detalles=json.dumps(detalles_extra, ensure_ascii=False),
        evento=tipo_evento,
        presupuesto=presupuesto_dec,
        precio_cotizado=precio_estimado,  # calculado según la tabla de paquetes por invitados
    )

    messages.success(
        request,
        f'¡Gracias, {nombre}! Tu solicitud de cotización fue registrada con un estimado de '
        f'${precio_estimado:,.0f}'.replace(',', '.') +
        '. Esta es una cotización aproximada; te contactaremos pronto para confirmar los detalles.'
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

    nombre = request.POST.get('nombre', '').strip()
    apellidos = request.POST.get('apellidos', '').strip()
    email = request.POST.get('email', '').strip()
    telefono = request.POST.get('telefono', '').strip()
    mensaje = request.POST.get('mensaje', '').strip()

    if not nombre or not apellidos or not email or not mensaje:
        messages.error(request, 'Por favor completa los campos obligatorios del formulario.')
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
