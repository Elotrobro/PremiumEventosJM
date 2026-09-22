from django import forms
from django.contrib import admin
from django.contrib.auth.hashers import make_password

from .models import (Usuario, Cliente, ContactoSimple, ItemDecoracion,
                    CarritoSeleccion, DetalleCarrito, Cotizacion, DetalleCotizacion, FotoGaleria,Testimonio)

# ═══════════════════════════════════════════════════════════════════════
# Configuración del panel de administración de Django para todos los
# modelos de Bd_PremiumEventos. `core` no aporta nada aquí porque no
# tiene modelos propios (ver core/admin.py).
# ═══════════════════════════════════════════════════════════════════════


class UsuarioAdminForm(forms.ModelForm):
    """Muestra la contraseña como campo tipo password en el admin y evita
    que se vea/edite el hash guardado en la base de datos.

    Sin este formulario personalizado, el admin mostraría el campo
    `contrasena` tal cual está en el modelo: un CharField normal donde se
    vería el hash guardado en texto plano. Aquí se reemplaza por un
    PasswordInput y se deja opcional (required=False), porque al editar
    un usuario existente no siempre se quiere cambiar la contraseña.
    """
    contrasena = forms.CharField(
        label='Contraseña',
        widget=forms.PasswordInput(render_value=False),  # render_value=False: nunca precarga el valor guardado en el input
        required=False,
        help_text='Déjalo en blanco para mantener la contraseña actual.',
    )

    class Meta:
        model = Usuario
        fields = '__all__'

    def clean_contrasena(self):
        contrasena = self.cleaned_data.get('contrasena')
        # self.instance.pk is None ⇒ es un usuario NUEVO (todavía sin guardar);
        # en ese caso sí es obligatorio asignar una contraseña.
        if not contrasena and self.instance.pk is None:
            raise forms.ValidationError('Debes asignar una contraseña al crear un usuario nuevo.')
        return contrasena


@admin.register(Usuario)
class UsuarioAdmin(admin.ModelAdmin):
    form = UsuarioAdminForm  # usa el formulario de arriba en vez del generado automáticamente
    list_display = ('id_usuario', 'nombre_completo', 'correo_electronico', 'rol', 'ultimo_acceso', 'fecha_creacion')
    search_fields = ('nombre_completo', 'correo_electronico')
    list_filter = ('rol',)
    readonly_fields = ('ultimo_acceso', 'fecha_creacion')  # se llenan automáticamente por el sistema, no se editan a mano

    def save_model(self, request, obj, form, change):
        # Se sobreescribe el guardado por defecto del admin para decidir
        # qué hacer con la contraseña según si se escribió una nueva o no.
        nueva_contrasena = form.cleaned_data.get('contrasena')
        if nueva_contrasena:
            # Se ingresó una contraseña nueva en el formulario: se hashea
            # antes de guardarla (nunca se guarda en texto plano).
            obj.contrasena = make_password(nueva_contrasena)
        elif change:
            # Edición (change=True) sin tocar el campo de contraseña: se
            # conserva el hash que ya estaba guardado, en vez de dejarlo
            # vacío (que rompería el login del usuario).
            obj.contrasena = Usuario.objects.get(pk=obj.pk).contrasena
        super().save_model(request, obj, form, change)

@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('id_cliente', 'nombre_completo', 'telefono_whatsapp', 'usuario')
    search_fields = ('nombre_completo', 'correo_electronico')

@admin.register(ContactoSimple)
class ContactoSimpleAdmin(admin.ModelAdmin):
    # Hoy es la ÚNICA forma de ver los mensajes de contacto (no hay vista
    # pública que los guarde todavía, ver core/views.py → contacto()).
    list_display = ('nombre', 'email', 'telefono', 'fecha_contacto')
    search_fields = ('nombre', 'email')

@admin.register(ItemDecoracion)
class ItemDecoracionAdmin(admin.ModelAdmin):
    # Hoy es la ÚNICA forma de gestionar el catálogo de ítems (el catálogo
    # público en catalogo.html todavía no lee de este modelo).
    list_display = ('nombre', 'precio', 'estado')
    search_fields = ('nombre',)
    list_filter = ('estado',)  # filtro rápido por disponible / no disponible

# Inline para ver los detalles del carrito directamente dentro del carrito
# (evita tener que ir a la sección de "Detalle carrito" por separado).
class DetalleCarritoInline(admin.TabularInline):
    model = DetalleCarrito
    extra = 0  # no mostrar filas vacías extra para agregar por defecto

@admin.register(CarritoSeleccion)
class CarritoSeleccionAdmin(admin.ModelAdmin):
    list_display = ('id_carrito', 'usuario', 'estado', 'fecha_creacion')
    list_filter = ('estado',)
    inlines = [DetalleCarritoInline]

# Inline para ver los detalles de la cotización directamente dentro de la
# cotización (StackedInline: se muestra en formato de formulario vertical,
# más legible que TabularInline para un solo registro relacionado 1 a 1).
class DetalleCotizacionInline(admin.StackedInline):
    model = DetalleCotizacion
    extra = 0

@admin.register(Cotizacion)
class CotizacionAdmin(admin.ModelAdmin):
    # Listado con todos los datos clave de la cotización de un vistazo,
    # sin tener que entrar a cada registro.
    list_display = ('id_cotizacion', 'codigo_seguimiento', 'cliente','nombre_cliente','correo_cliente','telefono_cliente', 'fecha_evento','cantidad_invitados','tema_estilo','hora_inicio','hora_fin', 'ubicacion', 'estado')
    readonly_fields = ('codigo_seguimiento',)  # se autogenera en el primer guardado, ver Cotizacion.save()
    search_fields = ('cliente__nombre_completo',)  # búsqueda a través de la relación con Cliente
    list_filter = ('fecha_evento', 'estado')
    inlines = [DetalleCotizacionInline]  # muestra presupuesto, precio cotizado y servicios solicitados en la misma pantalla

@admin.register(FotoGaleria)
class FotoGaleriaAdmin(admin.ModelAdmin):
    # La forma normal de gestionar esto es el panel de administrador propio
    # (panel_admin), no este admin de Django; queda registrado aquí solo
    # como respaldo/consulta rápida.
    list_display = ('id_foto', 'categoria', 'imagen', 'fecha_subida')
    list_filter = ('categoria',)

@admin.register(Testimonio)
class TestimonioAdmin(admin.ModelAdmin):
    list_display = (
        "usuario",
        "calificacion",
        "aprobado",
        "activo",
        "fecha_creacion",
    )

    list_filter = (
        "aprobado",
        "activo",
        "calificacion",
    )

    search_fields = (
        "usuario__nombre_completo",
        "comentario",
    )