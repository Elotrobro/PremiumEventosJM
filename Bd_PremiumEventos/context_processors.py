from django.conf import settings


def google_login(request):
    """
    Deja GOOGLE_CLIENT_ID disponible en todas las plantillas: base.html solo
    muestra el botón "Continuar con Google" si está configurado en el .env.
    """
    return {'google_client_id': settings.GOOGLE_CLIENT_ID}
