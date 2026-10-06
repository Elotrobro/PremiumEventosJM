"""
Verificación del correo al crear una cuenta.

registro_view (views.py) ya no crea la cuenta directamente: valida los
datos, los guarda en la sesión como "registro pendiente" (con la
contraseña ya hasheada) y envía un código de 6 dígitos al correo. La
cuenta (Usuario) solo se crea cuando la persona escribe el código
correcto en /registro/verificar/, así que nunca quedan en la base de datos
cuentas con correos que nadie confirmó.

  - El código vence en MINUTOS_VALIDEZ minutos.
  - Se permiten MAX_INTENTOS intentos por código; luego hay que pedir otro.
  - "Reenviar código" se puede usar cada SEGUNDOS_ENTRE_REENVIOS segundos,
    hasta MAX_REENVIOS veces.

El correo lo envía n8n por el mismo webhook de los recordatorios
(N8N_WEBHOOK_RECORDATORIOS_URL: Django arma el HTML y n8n solo lo envía).
Si no está configurado o n8n falla, lo envía Django con la configuración
EMAIL_* de settings.py (en local, se imprime en la consola de runserver).
"""

import hashlib
import hmac
import logging
import secrets
import time

from django.conf import settings
from django.contrib import messages
from django.core.mail import send_mail
from django.shortcuts import redirect, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from .models import Usuario
from .n8n import enviar_a_n8n

logger = logging.getLogger(__name__)

CLAVE_SESION = 'registro_pendiente'
MINUTOS_VALIDEZ = 15
MAX_INTENTOS = 5
SEGUNDOS_ENTRE_REENVIOS = 60
MAX_REENVIOS = 5
# Los mensajes de la página de verificación se muestran dentro de la tarjeta,
# no arriba de la página (ver base.html y registro/verificar_correo.html).
ETIQUETA = 'verificacion'


def _hash_codigo(codigo):
    # El código no se guarda tal cual en la sesión, sino firmado con la SECRET_KEY.
    return hmac.new(settings.SECRET_KEY.encode(), codigo.encode(), hashlib.sha256).hexdigest()


def _nuevo_codigo(pendiente):
    """Genera un código nuevo, lo deja en `pendiente` y lo devuelve (para enviarlo)."""
    codigo = f'{secrets.randbelow(10 ** 6):06d}'
    pendiente.update({
        'codigo': _hash_codigo(codigo),
        'vence': time.time() + MINUTOS_VALIDEZ * 60,
        'intentos': 0,
        'enviado': time.time(),
    })
    return codigo


def _enviar_codigo(nombre, correo, codigo):
    contexto = {'nombre': nombre.split()[0] if nombre else '', 'codigo': codigo, 'minutos': MINUTOS_VALIDEZ}
    asunto = f'{codigo} es tu código de verificación - Premium Eventos JM'
    if settings.N8N_WEBHOOK_RECORDATORIOS_URL:
        try:
            enviar_a_n8n(settings.N8N_WEBHOOK_RECORDATORIOS_URL, {
                'tipo': 'codigo_verificacion',
                'destinatario': 'cliente',
                'correo': correo,
                'asunto': asunto,
                'html': render_to_string('registro/correo_codigo.html', contexto),
            })
            return
        except Exception:
            logger.exception('n8n no respondió; el código de verificación se envía desde Django.')
    send_mail(asunto, render_to_string('registro/correo_codigo.txt', contexto), None, [correo])


def iniciar_verificacion(request, nombre, correo, contrasena_hash):
    """Lo llama registro_view cuando los datos del formulario son válidos."""
    pendiente = {'nombre': nombre, 'correo': correo, 'contrasena': contrasena_hash, 'reenvios': 0}
    codigo = _nuevo_codigo(pendiente)
    request.session[CLAVE_SESION] = pendiente
    _enviar_codigo(nombre, correo, codigo)


def _correo_oculto(correo):
    """jeanpaul446688@gmail.com → je***********@gmail.com"""
    usuario, _, dominio = correo.partition('@')
    return usuario[:2] + '*' * max(len(usuario) - 2, 3) + '@' + dominio


def verificar_correo(request):
    pendiente = request.session.get(CLAVE_SESION)
    if not pendiente:
        return redirect(f"{reverse('inicio')}?registro=1")

    if request.method == 'POST':
        codigo = ''.join(c for c in request.POST.get('codigo', '') if c.isdigit())

        if time.time() > pendiente['vence']:
            messages.error(request, 'El código venció. Pide uno nuevo con "Reenviar código".', extra_tags=ETIQUETA)
        elif pendiente['intentos'] >= MAX_INTENTOS:
            messages.error(request, 'Demasiados intentos con este código. Pide uno nuevo con "Reenviar código".', extra_tags=ETIQUETA)
        elif not hmac.compare_digest(_hash_codigo(codigo), pendiente['codigo']):
            pendiente['intentos'] += 1
            request.session[CLAVE_SESION] = pendiente
            restantes = MAX_INTENTOS - pendiente['intentos']
            messages.error(request, f'El código no es correcto. Te quedan {restantes} intento(s).'
                           if restantes else 'El código no es correcto. Pide uno nuevo con "Reenviar código".',
                           extra_tags=ETIQUETA)
        elif Usuario.objects.filter(correo_electronico__iexact=pendiente['correo']).exists():
            # Alguien terminó de registrar ese mismo correo mientras tanto.
            request.session.pop(CLAVE_SESION, None)
            messages.error(request, 'Ya existe una cuenta con ese correo. Inicia sesión o recupera tu contraseña.',
                           extra_tags='login-error')
            return redirect(f"{reverse('inicio')}?login=1")
        else:
            usuario = Usuario.objects.create(
                nombre_completo=pendiente['nombre'],
                correo_electronico=pendiente['correo'],
                contrasena=pendiente['contrasena'],
                rol='cliente',
                ultimo_acceso=timezone.now(),
            )
            request.session.pop(CLAVE_SESION, None)
            request.session.pop('registro_prefill', None)
            request.session['usuario_id'] = usuario.id_usuario
            request.session['usuario_nombre'] = usuario.nombre_completo
            request.session['usuario_rol'] = usuario.rol
            messages.success(request, f'¡Bienvenido, {usuario.nombre_completo}! Tu correo fue verificado y tu cuenta quedó creada.')
            return redirect('inicio')
        return redirect('verificar_correo')

    espera = int(pendiente['enviado'] + SEGUNDOS_ENTRE_REENVIOS - time.time())
    return render(request, 'registro/verificar_correo.html', {
        'correo_oculto': _correo_oculto(pendiente['correo']),
        'minutos': MINUTOS_VALIDEZ,
        'espera_reenvio': max(espera, 0),
        'puede_reenviar': pendiente['reenvios'] < MAX_REENVIOS,
    })


@require_POST
def reenviar_codigo(request):
    pendiente = request.session.get(CLAVE_SESION)
    if not pendiente:
        return redirect(f"{reverse('inicio')}?registro=1")

    if pendiente['reenvios'] >= MAX_REENVIOS:
        messages.error(request, 'Ya pediste demasiados códigos. Vuelve a registrarte en unos minutos.', extra_tags=ETIQUETA)
    elif time.time() < pendiente['enviado'] + SEGUNDOS_ENTRE_REENVIOS:
        messages.error(request, f'Espera {SEGUNDOS_ENTRE_REENVIOS} segundos entre cada reenvío.', extra_tags=ETIQUETA)
    else:
        codigo = _nuevo_codigo(pendiente)
        pendiente['reenvios'] += 1
        request.session[CLAVE_SESION] = pendiente
        _enviar_codigo(pendiente['nombre'], pendiente['correo'], codigo)
        messages.success(request, 'Te enviamos un código nuevo. Revisa también la carpeta de spam.', extra_tags=ETIQUETA)
    return redirect('verificar_correo')


@require_POST
def cancelar_registro(request):
    """"Usar otro correo": descarta el registro pendiente y vuelve a la pestaña de registro."""
    request.session.pop(CLAVE_SESION, None)
    return redirect(f"{reverse('inicio')}?registro=1")
