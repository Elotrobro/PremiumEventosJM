"""
Recordatorios automáticos por correo (los envía n8n).

Una vez al día se revisan las cotizaciones y se arma cada correo que toca:

  - cliente_3_dias / cliente_1_dia → al cliente, 3 días y 1 día antes de su evento.
  - cliente_dia_evento            → al cliente, el mismo día (estilo celebración).
  - cliente_despues               → al cliente, el día siguiente, invitándolo a dejar su testimonio.
  - resumen_admin                 → a la administradora: eventos de los próximos días
                                    y cotizaciones que siguen pendientes.

Aquí también está enviar_correo_estado: el aviso al cliente cuando el
admin aprueba o rechaza su cotización (lo llama el panel, no la tarea diaria).

Los correos al cliente solo salen para cotizaciones aprobadas o pagadas
(y completadas, en el caso del día siguiente). Django renderiza el HTML con
las plantillas de core/templates/recordatorios/ y le pasa a n8n un JSON por
correo: {tipo, destinatario, correo, asunto, html}. n8n solo lo envía.

Cada recordatorio enviado queda en RecordatorioEnviado, así que correr la
tarea dos veces el mismo día no repite correos. Se puede correr de dos
formas:
  - python manage.py enviar_recordatorios   (a mano o con el Programador de tareas)
  - POST a /recordatorios/ejecutar/ con el encabezado X-Webhook-Secret
    (lo usa el nodo Schedule Trigger de n8n cuando el sitio esté publicado).
"""

import hmac
import logging
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from django.conf import settings
from django.http import HttpResponseForbidden, JsonResponse
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from panel_admin.utils import formatear_miles

from .models import Cotizacion, RecordatorioEnviado
from .n8n import enviar_a_n8n

logger = logging.getLogger(__name__)

# El servidor guarda las fechas en UTC (TIME_ZONE = 'UTC'); "hoy" para los
# recordatorios es el día en Colombia, que es donde ocurren los eventos.
ZONA_NEGOCIO = ZoneInfo('America/Bogota')

DIAS_RESUMEN_ADMIN = 7       # el resumen muestra los eventos de los próximos 7 días
DIAS_PENDIENTE_ALERTA = 3    # una cotización pendiente con 3 días o más aparece como "sin atender"

ESTADOS_CONFIRMADOS = [Cotizacion.ESTADO_APROBADA, Cotizacion.ESTADO_PAGADO]

DIAS_SEMANA = ['lunes', 'martes', 'miércoles', 'jueves', 'viernes', 'sábado', 'domingo']
MESES = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio',
         'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre']


def fecha_larga(fecha):
    """date(2026, 12, 5) → "sábado 5 de diciembre" (LANGUAGE_CODE es inglés, por eso a mano)."""
    return f'{DIAS_SEMANA[fecha.weekday()]} {fecha.day} de {MESES[fecha.month - 1]}'


def hoy_negocio():
    return datetime.now(ZONA_NEGOCIO).date()


def _url(nombre, *args):
    return settings.SITIO_URL.rstrip('/') + reverse(nombre, args=args)


def _datos_evento(cotizacion):
    """Lo que las plantillas necesitan de una cotización, ya formateado."""
    detalle = cotizacion.detallecotizacion_set.first()
    return {
        'codigo': cotizacion.codigo_seguimiento,
        'nombre': cotizacion.nombre_cliente,
        'primer_nombre': cotizacion.nombre_cliente.split()[0] if cotizacion.nombre_cliente else '',
        'correo': cotizacion.correo_cliente,
        'telefono': cotizacion.telefono_cliente,
        'tipo_evento': detalle.evento.capitalize() if detalle else 'Evento',
        'tipo_evento_min': detalle.evento.lower() if detalle else 'evento',
        'fecha': fecha_larga(cotizacion.fecha_evento),
        'fecha_corta': cotizacion.fecha_evento.strftime('%d/%m/%Y'),
        'hora_inicio': cotizacion.hora_inicio.strftime('%H:%M'),
        'hora_fin': cotizacion.hora_fin.strftime('%H:%M'),
        'ubicacion': cotizacion.ubicacion,
        'invitados': cotizacion.cantidad_invitados,
        'tema': cotizacion.tema_estilo,
        'estado': cotizacion.get_estado_display(),
        'enlace_panel': _url('panel_admin:cotizacion_edit', cotizacion.pk),
    }


def recordatorios_pendientes(hoy):
    """
    Lista de (clave, datos_para_n8n) de todo lo que toca enviar `hoy` y
    todavía no se ha enviado. No envía nada; sirve también para --simular.
    """
    ya_enviados = set(RecordatorioEnviado.objects.values_list('clave', flat=True))
    pendientes = []

    def agregar(clave, destinatario, correo, asunto, plantilla, contexto, tipo):
        if clave in ya_enviados:
            return
        pendientes.append((clave, {
            'tipo': tipo,
            'destinatario': destinatario,
            'correo': correo,
            'asunto': asunto,
            'html': render_to_string(plantilla, contexto),
        }))

    # ---- Correos al cliente ----
    reglas_cliente = [
        # (tipo, día del evento relativo a hoy, estados, asunto, plantilla)
        ('cliente_3_dias', 3, ESTADOS_CONFIRMADOS,
         '¡Faltan 3 días para tu {tipo_evento_min}!', 'recordatorios/cliente_antes.html'),
        ('cliente_1_dia', 1, ESTADOS_CONFIRMADOS,
         '¡Mañana es tu {tipo_evento_min}!', 'recordatorios/cliente_antes.html'),
        ('cliente_dia_evento', 0, ESTADOS_CONFIRMADOS,
         '🎉 ¡Hoy es el gran día, {primer_nombre}!', 'recordatorios/cliente_dia_evento.html'),
        ('cliente_despues', -1, ESTADOS_CONFIRMADOS + [Cotizacion.ESTADO_COMPLETADA],
         '¿Cómo te fue en tu {tipo_evento_min}? Cuéntanos', 'recordatorios/cliente_despues.html'),
    ]
    for tipo, dias, estados, asunto, plantilla in reglas_cliente:
        cotizaciones = (Cotizacion.objects
                        .filter(fecha_evento=hoy + timedelta(days=dias), estado__in=estados)
                        .prefetch_related('detallecotizacion_set'))
        for cotizacion in cotizaciones:
            evento = _datos_evento(cotizacion)
            contexto = {'evento': evento, 'dias': dias, 'enlace_testimonios': _url('testimonios')}
            agregar(f'{tipo}:{cotizacion.pk}', 'cliente', cotizacion.correo_cliente,
                    asunto.format(**evento), plantilla, contexto, tipo)

    # ---- Resumen diario para la administradora ----
    proximos = (Cotizacion.objects
                .filter(fecha_evento__range=(hoy, hoy + timedelta(days=DIAS_RESUMEN_ADMIN)),
                        estado__in=ESTADOS_CONFIRMADOS)
                .order_by('fecha_evento', 'hora_inicio')
                .prefetch_related('detallecotizacion_set'))
    limite_pendiente = timezone.now() - timedelta(days=DIAS_PENDIENTE_ALERTA)
    sin_atender = (Cotizacion.objects
                   .filter(estado=Cotizacion.ESTADO_PENDIENTE,
                           detallecotizacion__fecha_cotizacion__lte=limite_pendiente)
                   .distinct()
                   .order_by('fecha_evento')
                   .prefetch_related('detallecotizacion_set'))
    proximos = [_datos_evento(c) for c in proximos]
    sin_atender = [_datos_evento(c) for c in sin_atender]
    if proximos or sin_atender:
        contexto = {
            'hoy': fecha_larga(hoy),
            'proximos': proximos,
            'sin_atender': sin_atender,
            'dias_resumen': DIAS_RESUMEN_ADMIN,
            'dias_pendiente': DIAS_PENDIENTE_ALERTA,
            'enlace_cotizaciones': _url('panel_admin:cotizaciones_list'),
        }
        asunto = (f'Resumen del {fecha_larga(hoy)}: {len(proximos)} evento(s) próximo(s), '
                  f'{len(sin_atender)} pendiente(s) sin atender')
        agregar(f'resumen_admin:{hoy.isoformat()}', 'administradora', '', asunto,
                'recordatorios/resumen_admin.html', contexto, 'resumen_admin')

    return pendientes


def enviar_recordatorios(hoy=None):
    """
    Envía a n8n todo lo pendiente de `hoy`. Un recordatorio solo se marca
    como enviado si n8n lo recibió; si falla, se vuelve a intentar la
    próxima vez que se corra la tarea ese mismo día.
    """
    if not settings.N8N_WEBHOOK_RECORDATORIOS_URL:
        raise RuntimeError('Falta N8N_WEBHOOK_RECORDATORIOS_URL en el .env.')

    enviados, fallidos = [], []
    for clave, datos in recordatorios_pendientes(hoy or hoy_negocio()):
        try:
            enviar_a_n8n(settings.N8N_WEBHOOK_RECORDATORIOS_URL, datos)
        except Exception:
            logger.exception('n8n no respondió; no se envió el recordatorio %s.', clave)
            fallidos.append(clave)
            continue
        RecordatorioEnviado.objects.create(clave=clave)
        enviados.append(clave)
    return {'enviados': enviados, 'fallidos': fallidos}


def enviar_correo_estado(cotizacion):
    """
    Avisa al cliente que su cotización fue aprobada (con los siguientes
    pasos) o rechazada (con el motivo, si se escribió). Se llama desde el
    panel cuando el admin cambia el estado a uno de esos dos. Usa el mismo
    webhook de los recordatorios: n8n solo envía el HTML que llega.

    Devuelve True si n8n lo recibió, False si no hay URL configurada o si
    n8n falló (el cambio de estado se guarda igual).
    """
    plantillas = {
        Cotizacion.ESTADO_APROBADA: ('cotizacion_aprobada', '¡Tu cotización {codigo} fue aprobada! 🎉',
                                     'recordatorios/cotizacion_aprobada.html'),
        Cotizacion.ESTADO_RECHAZADA: ('cotizacion_rechazada', 'Sobre tu cotización {codigo}',
                                      'recordatorios/cotizacion_rechazada.html'),
    }
    if cotizacion.estado not in plantillas or not settings.N8N_WEBHOOK_RECORDATORIOS_URL:
        return False

    tipo, asunto, plantilla = plantillas[cotizacion.estado]
    evento = _datos_evento(cotizacion)
    detalle = cotizacion.detallecotizacion_set.first()
    contexto = {
        'evento': evento,
        'precio_estimado': formatear_miles(detalle.precio_cotizado) if detalle else None,
        'motivo': cotizacion.motivo_rechazo.strip(),
        'enlace_inicio': _url('inicio'),
    }
    try:
        enviar_a_n8n(settings.N8N_WEBHOOK_RECORDATORIOS_URL, {
            'tipo': tipo,
            'destinatario': 'cliente',
            'correo': cotizacion.correo_cliente,
            'asunto': asunto.format(**evento),
            'html': render_to_string(plantilla, contexto),
        })
    except Exception:
        logger.exception('n8n no respondió; no se envió el correo de %s.', tipo)
        return False
    return True


@csrf_exempt
@require_POST
def ejecutar_recordatorios(request):
    """Lo llama n8n (Schedule Trigger + HTTP Request) con la misma clave de los webhooks."""
    secreto = settings.N8N_WEBHOOK_SECRET
    recibido = request.headers.get('X-Webhook-Secret', '')
    if not secreto or not hmac.compare_digest(recibido, secreto):
        return HttpResponseForbidden('Clave inválida.')
    try:
        resultado = enviar_recordatorios()
    except RuntimeError as error:
        return JsonResponse({'error': str(error)}, status=500)
    return JsonResponse(resultado)
