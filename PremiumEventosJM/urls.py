from django.contrib import admin
from django.urls import path
from core import views
from Bd_PremiumEventos import views as auth_views  # alias: son las vistas que sí tocan la base de datos (login/cotización)

# ═══════════════════════════════════════════════════════════════════════
# Tabla de rutas del proyecto (URLconf principal).
#
# No se usa include() por app: todas las rutas de core y Bd_PremiumEventos
# están centralizadas en este único archivo, mezclando ambas apps según
# cuál vista corresponda a cada URL.
# ═══════════════════════════════════════════════════════════════════════
urlpatterns = [
    path('admin/', admin.site.urls),  # panel de administración nativo de Django

    # ---- Rutas de solo lectura (app core): cada una solo renderiza un template ----
    path('', views.inicio, name='inicio'),
    path('informacion/', views.informacion, name='informacion'),
    path('galeria/', views.galeria, name='galeria'),
    path('testimonios/', views.testimonios, name='testimonios'),
    path('convenios/', views.convenios, name='convenios'),
    path('catalogo/', views.catalogo, name='catalogo'),
    path('contacto/', views.contacto, name='contacto'),

    # ---- Rutas que sí acceden a la base de datos (app Bd_PremiumEventos) ----
    path('cotizacion/', auth_views.cotizacion_view, name='cotizacion'),  # procesa el formulario modal de inicio.html (requiere sesión)
    path('login/', auth_views.login_view, name='login'),
    path('logout/', auth_views.logout_view, name='logout'),
]
