from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
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
    path('galeria/<slug:slug>/', views.galeria_categoria, name='galeria_categoria'),  # galería de un tipo de evento
    path('testimonios/', views.testimonios, name='testimonios'),
    path('convenios/', views.convenios, name='convenios'),
    path('catalogo/', views.catalogo, name='catalogo'),
    path('contacto/', views.contacto, name='contacto'),

    # ---- Rutas que sí acceden a la base de datos (app Bd_PremiumEventos) ----
    path('cotizacion/', auth_views.cotizacion_view, name='cotizacion'),  # procesa el formulario modal de inicio.html (requiere sesión)
    path('contacto/enviar/', auth_views.guardar_contacto, name='guardar_contacto'),  # procesa el formulario de contacto.html
    path('login/', auth_views.login_view, name='login'),
    path('registro/', auth_views.registro_view, name='registro'),  # crea cuentas de cliente desde la modal
    path('logout/', auth_views.logout_view, name='logout'),

    # ---- Panel de administrador a medida (CRUD, historial y reportes PDF) ----
    path('panel-admin/', include('panel_admin.urls')),

    path("testimonios/",auth_views.testimonios,name="testimonios"),
]

if settings.DEBUG:
    # Sirve /media/ (fotos de la galería subidas desde el panel) en
    # desarrollo. En producción esto lo debe servir el servidor web, no Django.
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
