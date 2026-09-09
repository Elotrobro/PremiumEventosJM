from django import forms
from django.contrib.auth.hashers import make_password

from Bd_PremiumEventos.models import Usuario, ItemDecoracion, Cotizacion


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
            'rol': forms.Select(choices=[('admin', 'Administrador'), ('cliente', 'Cliente')],
                                 attrs={'class': 'form-control'}),
        }

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
        fields = ['nombre', 'descripcion', 'precio', 'estado']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'precio': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'estado': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {'estado': 'Disponible para alquilar'}


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
