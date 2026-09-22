from django.urls import path

from . import views

app_name = 'panel_admin'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),

    # Usuarios
    path('usuarios/', views.usuarios_list, name='usuarios_list'),
    path('usuarios/nuevo/', views.usuario_create, name='usuario_create'),
    path('usuarios/<int:pk>/editar/', views.usuario_edit, name='usuario_edit'),
    path('usuarios/<int:pk>/eliminar/', views.usuario_delete, name='usuario_delete'),

    # Catálogo de decoración
    path('catalogo/', views.catalogo_list, name='catalogo_list'),
    path('catalogo/nuevo/', views.catalogo_create, name='catalogo_create'),
    path('catalogo/<int:pk>/editar/', views.catalogo_edit, name='catalogo_edit'),
    path('catalogo/<int:pk>/eliminar/', views.catalogo_delete, name='catalogo_delete'),

    # Galería
    path('galeria/', views.galeria_list, name='galeria_list'),
    path('galeria/subir/', views.galeria_upload, name='galeria_upload'),
    path('galeria/<int:pk>/eliminar/', views.galeria_delete, name='galeria_delete'),

    # Mensajes de contacto
    path('mensajes/', views.mensajes_list, name='mensajes_list'),
    path('mensajes/<int:pk>/eliminar/', views.mensaje_delete, name='mensaje_delete'),

    # Testimonios
    path('testimonios/', views.testimonios_list, name='testimonios_list'),
    path('testimonios/nuevo/', views.testimonio_create, name='testimonio_create'),
    path('testimonios/<int:pk>/editar/', views.testimonio_edit, name='testimonio_edit'),
    path('testimonios/<int:pk>/eliminar/', views.testimonio_delete, name='testimonio_delete'),

    # Cotizaciones
    path('cotizaciones/', views.cotizaciones_list, name='cotizaciones_list'),
    path('cotizaciones/<int:pk>/editar/', views.cotizacion_edit, name='cotizacion_edit'),
    path('cotizaciones/<int:pk>/eliminar/', views.cotizacion_delete, name='cotizacion_delete'),

    # Historial y reportes
    path('historial/', views.historial_list, name='historial_list'),
    path('historial/pdf/', views.historial_pdf, name='historial_pdf'),

    
]
