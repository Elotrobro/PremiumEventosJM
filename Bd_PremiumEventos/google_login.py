"""
Iniciar sesión o crear cuenta con Google ("Continuar con Google").

Cómo funciona:
  1. En la modal de cuenta (base.html) el botón oficial de Google abre una
     ventana donde la persona elige su cuenta (core/static/js/google-login.js).
  2. Google le entrega al navegador un "ID token" firmado, que el JS envía
     aquí por POST (con el token CSRF de Django, como cualquier formulario).
  3. Este módulo verifica el token con la librería oficial google-auth: que
     lo firmó Google, que no venció, que es para NUESTRO GOOGLE_CLIENT_ID y
     que Google ya verificó el correo.
  4. Con el correo:
       - si ya hay una cuenta (aunque se haya creado con contraseña), entra
         a esa misma cuenta;
       - si no hay, crea una cuenta de cliente al instante. No se pide el
         código de 6 dígitos de verificacion.py porque Google ya confirmó
         que el correo es de esa persona.
     Las cuentas creadas así no tienen contraseña (contraseña "inutilizable"
     de Django). Si después quieren una, usan "¿Olvidaste tu contraseña?".

Solo hace falta GOOGLE_CLIENT_ID en el .env (ver settings.py y .env.example);
el "secreto de cliente" de Google no se usa.
"""

import logging

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.hashers import make_password
from django.shortcuts import redirect
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST
from google.auth import exceptions as google_exceptions
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token

from . import limpieza, verificacion
from .models import Usuario
from .validaciones import SIGNOS_PERMITIDOS_NOMBRE, errores_nombre, limpiar_nombre

logger = logging.getLogger(__name__)

LARGO_MAXIMO_NOMBRE = 150   # Usuario.nombre_completo
LARGO_MAXIMO_CORREO = 100   # Usuario.correo_electronico


def _nombre_desde_google(datos, correo):
    """
    Nombre para una cuenta nueva. Se usa el de la cuenta de Google, dejando
    solo letras y los signos que el sitio acepta en nombres (validaciones.py).
    Si no queda un nombre válido (ej. un apodo con números o emojis), se usa
    la parte del correo antes de la @.
    """
    candidatos = [
        datos.get('name', ''),
        f"{datos.get('given_name', '')} {datos.get('family_name', '')}",
        correo.split('@')[0].replace('.', ' ').replace('_', ' '),
    ]
    for candidato in candidatos:
        nombre = limpiar_nombre(''.join(
            c for c in candidato if c.isalpha() or c in SIGNOS_PERMITIDOS_NOMBRE
        ))[:LARGO_MAXIMO_NOMBRE].strip()
        if not errores_nombre(nombre):
            return nombre
    return 'Cliente'


def _iniciar_sesion(request, usuario):
    """Lo mismo que hace login_view (views.py) cuando la contraseña es correcta."""
    usuario.ultimo_acceso = timezone.now()
    usuario.save(update_fields=['ultimo_acceso'])

    # Nueva clave de sesión al iniciar sesión (evita reutilizar una anterior).
    request.session.cycle_key()
    request.session['usuario_id'] = usuario.id_usuario
    request.session['usuario_nombre'] = usuario.nombre_completo
    request.session['usuario_rol'] = usuario.rol

    # Restos de un login o registro con contraseña que quedó a medias.
    for clave in ('login_correo_prefill', 'registro_prefill', verificacion.CLAVE_SESION):
        request.session.pop(clave, None)


@require_POST
def google_login_view(request):
    origen = 'registro' if request.POST.get('origen') == 'registro' else 'login'
    url_error = f"{reverse('inicio')}?{origen}=1"

    def error(texto):
        messages.error(request, texto, extra_tags=f'{origen}-error')
        return redirect(url_error)

    if request.session.get('usuario_id'):
        return redirect('inicio')

    if not settings.GOOGLE_CLIENT_ID:
        return error('El inicio de sesión con Google no está disponible en este momento.')

    credencial = request.POST.get('credential', '')
    if not credencial:
        return error('No recibimos la respuesta de Google. Intenta de nuevo.')

    try:
        datos = id_token.verify_oauth2_token(
            credencial,
            google_requests.Request(),
            settings.GOOGLE_CLIENT_ID,
            clock_skew_in_seconds=10,  # tolera relojes con unos segundos de diferencia
        )
    except google_exceptions.TransportError:
        logger.exception('No se pudo contactar a Google para verificar el inicio de sesión.')
        return error('No pudimos comunicarnos con Google. Revisa tu conexión e intenta de nuevo.')
    except ValueError:
        # Firma inválida, token vencido o emitido para otra aplicación.
        logger.warning('Token de Google rechazado.', exc_info=True)
        return error('No se pudo verificar tu cuenta de Google. Intenta de nuevo.')

    correo = (datos.get('email') or '').strip().lower()
    if not correo or not datos.get('email_verified'):
        return error('Tu cuenta de Google no tiene un correo verificado. Usa otro método para ingresar.')
    if len(correo) > LARGO_MAXIMO_CORREO:
        return error('Tu correo de Google es demasiado largo para registrarlo. Usa otro método para ingresar.')

    limpieza.ejecutar_si_toca()  # igual que login_view: clientes sin cotizar en 60 días

    usuario = Usuario.objects.filter(correo_electronico__iexact=correo).first()
    if usuario is not None:
        # Mismo correo que una cuenta existente (con o sin contraseña): entra
        # a esa cuenta. Google ya comprobó que la persona es dueña del correo.
        _iniciar_sesion(request, usuario)
        messages.success(request, f'¡Bienvenido, {usuario.nombre_completo}!')
        return redirect('inicio')

    usuario = Usuario.objects.create(
        nombre_completo=_nombre_desde_google(datos, correo),
        correo_electronico=correo,
        contrasena=make_password(None),  # sin contraseña: solo entra con Google (o la crea con "¿Olvidaste tu contraseña?")
        rol=Usuario.ROL_CLIENTE,
    )
    _iniciar_sesion(request, usuario)
    messages.success(
        request,
        f'¡Bienvenido, {usuario.nombre_completo}! Tu cuenta quedó creada con tu correo de Google.',
    )
    return redirect('inicio')
