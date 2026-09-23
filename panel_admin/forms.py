from django import forms
from django.contrib.auth.hashers import make_password

from Bd_PremiumEventos.models import Usuario, ItemDecoracion, Cotizacion, FotoGaleria


class UsuarioAdminForm(forms.ModelForm):
    """
    Formulario para crear/editar usuarios desde el panel de administrador
    (misma idea que Bd_PremiumEventos.admin.UsuarioAdminForm, pero
    reutilizable en las vistas propias del panel): la contraseña se pide
    aparte, se deja opcional al editar y se guarda siempre hasheada.
    """
    contrasena = forms.CharField(
        label='Contraseña',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Contraseña'}, render_value=False),
        required=False,
        help_text='Déjalo en blanco para mantener la contraseña actual.',
    )

    class Meta:
        model = Usuario
        fields = ['nombre_completo', 'correo_electronico', 'rol', 'contrasena']
        widgets = {
            'nombre_completo': forms.TextInput(attrs={'class': 'form-control'}),
            'correo_electronico': forms.EmailInput(attrs={'class': 'form-control'}),
            'rol': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, actor_rol=None, **kwargs):
        """
        `actor_rol` es el rol de quien está usando el formulario (viene de
        request.session['usuario_rol']). Un 'empleado' puede crear cuentas,
        pero no puede otorgarse a sí mismo ni a nadie el rol 'admin' ni
        'empleado' — solo puede registrar clientes. Esto evita que crear
        usuarios se convierta en una puerta trasera para auto-ascenderse.
        """
        super().__init__(*args, **kwargs)
        if actor_rol == 'empleado':
            self.fields['rol'].choices = [(Usuario.ROL_CLIENTE, 'Cliente')]
            self.fields['rol'].initial = Usuario.ROL_CLIENTE
        else:
            self.fields['rol'].choices = Usuario.ROL_CHOICES

    def clean_contrasena(self):
        contrasena = self.cleaned_data.get('contrasena')
        if not contrasena and self.instance.pk is None:
            raise forms.ValidationError('Debes asignar una contraseña al crear un usuario nuevo.')
        return contrasena

    def save(self, commit=True):
        usuario = super().save(commit=False)
        nueva_contrasena = self.cleaned_data.get('contrasena')
        if nueva_contrasena:
            usuario.contrasena = make_password(nueva_contrasena)
        if commit:
            usuario.save()
        return usuario


class ItemDecoracionForm(forms.ModelForm):
    class Meta:
        model = ItemDecoracion
        fields = ['nombre', 'descripcion', 'precio', 'categoria', 'unidad', 'imagen', 'estado']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'precio': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'categoria': forms.Select(attrs={'class': 'form-control'}),
            'unidad': forms.TextInput(attrs={'class': 'form-control'}),
            'imagen': forms.ClearableFileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'estado': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {'estado': 'Disponible para alquilar'}


class _VariosArchivosInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class _VariasImagenesField(forms.ImageField):
    """Como ImageField, pero acepta varios archivos a la vez: valida cada uno
    (que sea una imagen real) y devuelve la lista."""
    widget = _VariosArchivosInput

    def clean(self, data, initial=None):
        if isinstance(data, (list, tuple)) and data:
            return [super(_VariasImagenesField, self).clean(archivo, initial) for archivo in data]
        if isinstance(data, (list, tuple)):
            data = None  # ningún archivo: que dispare el error de "campo obligatorio"
        return [super().clean(data, initial)]


class SubirFotosGaleriaForm(forms.Form):
    """Sube varias fotos de una vez a la misma categoría de la galería."""
    categoria = forms.ChoiceField(
        label='Categoría',
        choices=FotoGaleria._meta.get_field('categoria').choices,
        widget=forms.Select(attrs={'class': 'form-control'}),
    )
    imagenes = _VariasImagenesField(
        label='Imágenes',
        help_text='Puedes seleccionar varias a la vez (Ctrl o Shift + clic).',
        error_messages={
            'required': 'Selecciona al menos una imagen.',
            'invalid_image': 'Uno de los archivos no es una imagen válida.',
        },
        widget=_VariosArchivosInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
    )


class CotizacionEstadoForm(forms.ModelForm):
    """
    Edición reducida de una cotización desde el panel: el admin solo
    gestiona el estado y sus notas internas; los datos que escribió el
    cliente (fecha, invitados, ubicación, etc.) no se tocan aquí.
    """
    class Meta:
        model = Cotizacion
        fields = ['estado', 'notas_admin']
        widgets = {
            'estado': forms.Select(attrs={'class': 'form-control'}),
            'notas_admin': forms.Textarea(attrs={'class': 'form-control', 'rows': 4,
                                                'placeholder': 'Notas internas (no visibles para el cliente)'}),
        }
