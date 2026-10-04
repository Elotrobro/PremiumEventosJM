"""
Chatbot del sitio (burbuja "JM" de base.html → core/static/js/widget.js).

Reparto del trabajo:
  - Django (aquí) es quien sabe: arma las instrucciones del asistente con
    la información real del negocio (core/templates/chatbot/instrucciones.txt),
    guarda el historial de la conversación en la sesión y, si el mensaje
    trae un código de seguimiento (PJM-AAAAMMDD-XXXXXX), consulta esa
    cotización en la base de datos.
  - n8n solo redacta: un AI Agent con DeepSeek recibe {instrucciones,
    historial, mensaje, contexto} y devuelve {respuesta}. Para estimar
    precios usa una herramienta (Code Tool, código en
    n8n/chatbot_calcular_precio.js) con la misma tabla de
    calcular_precio_estimado de views.py, así el modelo nunca inventa un valor.

Si N8N_WEBHOOK_CHATBOT_URL no está configurada o n8n falla, el chat no se
rompe: responde con un texto fijo (y con el estado de la cotización, si
el mensaje traía un código) e invita a escribir por WhatsApp.
"""

import json
import logging
import re

from django.conf import settings
from django.core.cache import cache
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.urls import reverse
from django.views.decorators.http import require_POST

from core.galeria_data import CATEGORIAS
from panel_admin.utils import formatear_miles

from .models import Cotizacion, ItemDecoracion
from .n8n import enviar_a_n8n
from .recordatorios import fecha_larga, hoy_negocio

logger = logging.getLogger(__name__)

LARGO_MAXIMO_MENSAJE = 500
MENSAJES_EN_HISTORIAL = 12            # últimos 6 intercambios (usuario + asistente)
LIMITE_MENSAJES, VENTANA_SEGUNDOS = 20, 5 * 60   # máx. 20 mensajes cada 5 minutos por IP

# Acepta el código con o sin guiones y en minúsculas: "pjm20261004b1fqhe".
CODIGO_RE = re.compile(r'\bPJM-?(\d{8})-?([A-Z0-9]{6})\b', re.IGNORECASE)

WHATSAPP = '311 775 81 62'

ESTADOS_PARA_CLIENTE = {
    Cotizacion.ESTADO_PENDIENTE: 'Pendiente: aún no ha sido revisada por el equipo.',
    Cotizacion.ESTADO_APROBADA: 'Aprobada: el equipo la revisó y la aprobó; falta confirmar detalles y el pago para reservar la fecha.',
    Cotizacion.ESTADO_RECHAZADA: 'No aprobada.',
    Cotizacion.ESTADO_PAGADO: 'Pagada: la fecha está reservada.',
    Cotizacion.ESTADO_COMPLETADA: 'Completada: el evento ya se realizó.',
}


def _url(nombre, *args):
    return settings.SITIO_URL.rstrip('/') + reverse(nombre, args=args)


def buscar_cotizacion(mensaje):
    """
    Si el mensaje trae un código de seguimiento, devuelve lo que se le
    puede mostrar al cliente de esa cotización. A propósito NO incluye
    nombre, correo ni teléfono: el código funciona como una guía de
    paquetería y cualquiera que lo tenga puede consultarlo.
    """
    coincidencia = CODIGO_RE.search(mensaje)
    if not coincidencia:
        return None
    codigo = f'PJM-{coincidencia.group(1)}-{coincidencia.group(2).upper()}'
    cotizacion = (Cotizacion.objects.filter(codigo_seguimiento=codigo)
                  .prefetch_related('detallecotizacion_set').first())
    if cotizacion is None:
        return {'codigo': codigo, 'encontrada': False}

    detalle = cotizacion.detallecotizacion_set.first()
    datos = {
        'codigo': codigo,
        'encontrada': True,
        'estado': ESTADOS_PARA_CLIENTE.get(cotizacion.estado, cotizacion.get_estado_display()),
        'tipo_evento': detalle.evento.capitalize() if detalle else 'Evento',
        'fecha_evento': fecha_larga(cotizacion.fecha_evento) + f' de {cotizacion.fecha_evento.year}',
        'hora': f'{cotizacion.hora_inicio:%H:%M} a {cotizacion.hora_fin:%H:%M}',
        'invitados': cotizacion.cantidad_invitados,
        'ubicacion': cotizacion.ubicacion,
        'precio_estimado': f'${formatear_miles(detalle.precio_cotizado)}' if detalle else 'Sin calcular',
    }
    if cotizacion.estado == Cotizacion.ESTADO_RECHAZADA and cotizacion.motivo_rechazo.strip():
        datos['motivo_no_aprobada'] = cotizacion.motivo_rechazo.strip()
    return datos


def instrucciones_asistente():
    """El "system prompt" del asistente, con la información real del sitio."""
    return render_to_string('chatbot/instrucciones.txt', {
        'tipos_evento': [c['nombre'] for c in CATEGORIAS if c['slug'] != 'alquiler-de-mobiliario'],
        'catalogo': ItemDecoracion.objects.filter(estado=True).order_by('categoria', 'nombre'),
        'whatsapp': WHATSAPP,
        'enlaces': {
            'inicio': _url('inicio'),
            'catalogo': _url('catalogo'),
            'galeria': _url('galeria'),
            'convenios': _url('convenios'),
            'contacto': _url('contacto'),
            'testimonios': _url('testimonios'),
            'informacion': _url('informacion'),
            'recuperar_password': _url('recuperar_password'),
        },
    })


def respuesta_sin_ia(cotizacion):
    """Lo que contesta el chat si n8n no está configurado o no responde."""
    if cotizacion and cotizacion['encontrada']:
        texto = (f'Tu cotización {cotizacion["codigo"]} ({cotizacion["tipo_evento"]}, '
                 f'{cotizacion["fecha_evento"]}) está en estado: {cotizacion["estado"]}')
        if cotizacion.get('motivo_no_aprobada'):
            texto += f'\nMotivo: {cotizacion["motivo_no_aprobada"]}'
        return texto + f'\n\nSi tienes alguna duda, escríbenos por WhatsApp al {WHATSAPP}.'
    if cotizacion:
        return (f'No encontré ninguna cotización con el código {cotizacion["codigo"]}. '
                'Revisa que esté bien escrito (ejemplo: PJM-20261004-B1FQHE).')
    return ('En este momento no puedo responder automáticamente 😔. '
            f'Escríbenos por WhatsApp al {WHATSAPP} y un asesor te atiende con gusto.')


def _limite_superado(request):
    clave = 'chatbot:' + request.META.get('REMOTE_ADDR', 'desconocida')
    cache.add(clave, 0, VENTANA_SEGUNDOS)
    try:
        return cache.incr(clave) > LIMITE_MENSAJES
    except ValueError:  # la clave venció justo entre add() e incr()
        return False


@require_POST
def chatbot_mensaje(request):
    """
    Recibe {"mensaje": "..."} desde widget.js y devuelve {"respuesta": "..."}.
    Con el envío normal del formulario va el token CSRF (ver base.html).
    """
    try:
        mensaje = str(json.loads(request.body).get('mensaje', '')).strip()
    except (ValueError, AttributeError):
        mensaje = ''
    if not mensaje:
        return JsonResponse({'error': 'Escribe un mensaje.'}, status=400)
    if len(mensaje) > LARGO_MAXIMO_MENSAJE:
        return JsonResponse({'error': f'El mensaje es muy largo (máximo {LARGO_MAXIMO_MENSAJE} caracteres).'}, status=400)
    if _limite_superado(request):
        return JsonResponse({'respuesta': 'Estás enviando muchos mensajes seguidos. Espera unos minutos, '
                                          f'o escríbenos por WhatsApp al {WHATSAPP}.'})

    historial = request.session.get('chatbot_historial', [])
    cotizacion = buscar_cotizacion(mensaje)

    respuesta = None
    if settings.N8N_WEBHOOK_CHATBOT_URL:
        try:
            resultado = enviar_a_n8n(settings.N8N_WEBHOOK_CHATBOT_URL, {
                'instrucciones': instrucciones_asistente(),
                'historial': historial,
                'mensaje': mensaje,
                'contexto': {
                    'fecha_hoy': fecha_larga(hoy_negocio()) + f' de {hoy_negocio().year}',
                    'sesion_iniciada': bool(request.session.get('usuario_id')),
                    'nombre_usuario': request.session.get('usuario_nombre', ''),
                    'cotizacion_consultada': cotizacion,
                },
            }, timeout=60)  # el modelo puede tardar varios segundos en contestar
            respuesta = (resultado or {}).get('respuesta', '').strip() or None
        except Exception:
            logger.exception('El chatbot de n8n no respondió.')
    if not respuesta:
        respuesta = respuesta_sin_ia(cotizacion)

    historial += [{'rol': 'usuario', 'texto': mensaje}, {'rol': 'asistente', 'texto': respuesta}]
    request.session['chatbot_historial'] = historial[-MENSAJES_EN_HISTORIAL:]
    return JsonResponse({'respuesta': respuesta})


@require_POST
def chatbot_reiniciar(request):
    """Borra la conversación guardada (botón "Nueva conversación" del chat)."""
    request.session.pop('chatbot_historial', None)
    return JsonResponse({'ok': True})
