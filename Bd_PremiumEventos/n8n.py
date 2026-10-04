"""
Envío de datos a los workflows de n8n.

Cada workflow empieza con un nodo Webhook protegido con Header Auth: Django
le hace un POST con un JSON y la clave N8N_WEBHOOK_SECRET en el encabezado
X-Webhook-Secret, y n8n arma y envía los correos. Todos los webhooks usan
la misma clave; lo único que cambia es la URL (una variable del .env por
workflow, ver settings.py).
"""

import json
import urllib.request

from django.conf import settings


def enviar_a_n8n(url, datos):
    """
    Hace el POST al webhook. Lanza una excepción si n8n no responde o
    responde con error, para que quien llama decida qué hacer en ese caso.
    """
    peticion = urllib.request.Request(
        url,
        data=json.dumps(datos, ensure_ascii=False).encode('utf-8'),
        method='POST',
        headers={'Content-Type': 'application/json', 'X-Webhook-Secret': settings.N8N_WEBHOOK_SECRET},
    )
    with urllib.request.urlopen(peticion, timeout=10):
        pass
