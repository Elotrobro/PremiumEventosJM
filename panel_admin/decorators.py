from functools import wraps

from django.contrib import messages
from django.shortcuts import redirect


def admin_required(view_func):
    """
    Protege una vista para que solo pueda entrar quien tenga una sesión
    activa con rol 'admin' (ver request.session['usuario_rol'], que se
    llena en Bd_PremiumEventos.views.login_view).

    No usa @login_required de django.contrib.auth porque el login del
    sitio no usa ese sistema: la sesión propia (usuario_id/usuario_rol)
    es la única fuente de verdad sobre quién está autenticado.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.session.get('usuario_id'):
            messages.error(request, 'Debes iniciar sesión para acceder al panel de administrador.')
            return redirect('login')

        if request.session.get('usuario_rol') != 'admin':
            messages.error(request, 'No tienes permisos para acceder al panel de administrador.')
            return redirect('inicio')

        return view_func(request, *args, **kwargs)

    return wrapper
