from functools import wraps

from django.contrib import messages
from django.shortcuts import redirect

# Roles que pueden entrar al panel de administrador. 'empleado' es un rol
# de confianza limitada: ve y gestiona casi todo igual que 'admin', pero
# con las restricciones que se aplican vista por vista (ver es_admin() y
# los comentarios en panel_admin/views.py) — principalmente no puede
# eliminar nada salvo clientes sin cotizaciones, ni editar cotizaciones
# ni cuentas de usuario.
ROLES_PANEL = ('admin', 'empleado')


def es_admin(request):
    """Atajo usado dentro de las vistas para las restricciones del rol empleado."""
    return request.session.get('usuario_rol') == 'admin'


def _requiere_sesion_de_panel(request, roles_permitidos):
    """
    Comprueba sesión activa + rol permitido. Devuelve None si todo está
    en orden, o un HttpResponse de redirección si hay que cortar la vista.
    """
    if not request.session.get('usuario_id'):
        messages.error(request, 'Debes iniciar sesión para acceder al panel de administrador.')
        return redirect('login')

    if request.session.get('usuario_rol') not in roles_permitidos:
        messages.error(request, 'No tienes permisos para acceder a esta sección del panel.')
        return redirect('panel_admin:dashboard' if request.session.get('usuario_rol') in ROLES_PANEL else 'inicio')

    return None


def admin_required(view_func):
    """
    Protege una vista para que solo pueda entrar quien tenga una sesión
    activa con rol 'admin' (ver request.session['usuario_rol'], que se
    llena en Bd_PremiumEventos.views.login_view). Se usa en las acciones
    que el rol 'empleado' tiene prohibidas: editar/eliminar cotizaciones,
    eliminar catálogo o mensajes, y editar cualquier usuario.

    No usa @login_required de django.contrib.auth porque el login del
    sitio no usa ese sistema: la sesión propia (usuario_id/usuario_rol)
    es la única fuente de verdad sobre quién está autenticado.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        respuesta = _requiere_sesion_de_panel(request, ('admin',))
        if respuesta is not None:
            return respuesta
        return view_func(request, *args, **kwargs)

    return wrapper


def staff_required(view_func):
    """
    Igual que admin_required, pero también deja pasar al rol 'empleado'.
    Es el decorador por defecto del panel: casi todas las pantallas se
    pueden VER con este rol; las restricciones puntuales (no eliminar,
    no editar cotizaciones/usuarios) se resuelven dentro de cada vista o
    se ocultan en la plantilla, no aquí.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        respuesta = _requiere_sesion_de_panel(request, ROLES_PANEL)
        if respuesta is not None:
            return respuesta
        return view_func(request, *args, **kwargs)

    return wrapper
