
from django import forms
from django.forms import modelformset_factory
from django.contrib.auth.hashers import make_password

from Bd_PremiumEventos.models import (
    Usuario,
    ItemDecoracion,
    Cotizacion,
    FotoGaleria,
    PaquetePrecio,
    ConfiguracionPrecios,
    ServicioPrecio,
)
from Bd_PremiumEventos.validaciones import REGLAS_CONTRASENA, errores_contrasena, errores_nombre, limpiar_nombre


class UsuarioAdminForm(forms.ModelForm):
    """
    Formulario para crear/editar usuarios desde el panel de administrador
    (misma idea que Bd_PremiumEventos.admin.UsuarioAdminForm, pero
    reutilizable en las vistas propias del panel): la contraseña se pide
    aparte, se deja opcional al editar y se guarda siempre hasheada.
    """

    contrasena = forms.CharField(
        label='Contraseña',
        widget=forms.PasswordInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Contraseña'
            },
            render_value=False
        ),
        required=False,
        help_text=f'Debe tener {REGLAS_CONTRASENA}. Al editar, déjalo en blanco para mantener la contraseña actual.',
    )

    class Meta:
        model = Usuario
        fields = [
            'nombre_completo',
            'correo_electronico',
            'rol',
            'contrasena'
        ]
        widgets = {
            'nombre_completo': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'pattern': "[A-Za-zÀ-ÖØ-öø-ÿ' .\\-]+",
                    'title': 'Solo letras y espacios (sin números, @ ni otros símbolos)',
                }
            ),
            'correo_electronico': forms.EmailInput(
                attrs={'class': 'form-control'}
            ),
            'rol': forms.Select(
                attrs={'class': 'form-control'}
            ),
        }

    def __init__(self, *args, actor_rol=None, **kwargs):
        """
        `actor_rol` es el rol de quien está usando el formulario
        (viene de request.session['usuario_rol']).

        Un 'empleado' puede crear cuentas, pero no puede otorgarse
        a sí mismo ni a nadie el rol 'admin' ni 'empleado'.
        Solo puede registrar clientes.
        """
        super().__init__(*args, **kwargs)

        if actor_rol == 'empleado':
            self.fields['rol'].choices = [
                (Usuario.ROL_CLIENTE, 'Cliente')
            ]
            self.fields['rol'].initial = Usuario.ROL_CLIENTE
        else:
            self.fields['rol'].choices = Usuario.ROL_CHOICES

    def clean_nombre_completo(self):
        nombre = limpiar_nombre(self.cleaned_data.get('nombre_completo', ''))
        errores = errores_nombre(nombre, 'el nombre completo')
        if errores:
            raise forms.ValidationError(errores)
        return nombre

    def clean_contrasena(self):
        contrasena = self.cleaned_data.get('contrasena')

        if not contrasena and self.instance.pk is None:
            raise forms.ValidationError(
                'Debes asignar una contraseña al crear un usuario nuevo.'
            )

        # Mismas reglas de contraseña segura que el registro (validaciones.py).
        if contrasena:
            errores = errores_contrasena(contrasena)
            if errores:
                raise forms.ValidationError(errores)

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

        fields = [
            'nombre',
            'descripcion',
            'precio',
            'categoria',
            'unidad',
            'imagen',
            'estado'
        ]

        widgets = {
            'nombre': forms.TextInput(
                attrs={'class': 'form-control'}
            ),
            'descripcion': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'rows': 4
                }
            ),
            'precio': forms.NumberInput(
                attrs={
                    'class': 'form-control',
                    'step': '0.01',
                    'min': '0'
                }
            ),
            'categoria': forms.Select(
                attrs={'class': 'form-control'}
            ),
            'unidad': forms.TextInput(
                attrs={'class': 'form-control'}
            ),
            'imagen': forms.ClearableFileInput(
                attrs={
                    'class': 'form-control',
                    'accept': 'image/*'
                }
            ),
            'estado': forms.CheckboxInput(
                attrs={'class': 'form-check-input'}
            ),
        }

        labels = {
            'estado': 'Disponible para alquilar'
        }


class _VariosArchivosInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class _VariasImagenesField(forms.ImageField):
    """
    Como ImageField, pero acepta varios archivos a la vez:
    valida cada uno y devuelve la lista.
    """

    widget = _VariosArchivosInput

    def clean(self, data, initial=None):

        if isinstance(data, (list, tuple)) and data:
            return [
                super(_VariasImagenesField, self).clean(
                    archivo,
                    initial
                )
                for archivo in data
            ]

        if isinstance(data, (list, tuple)):
            data = None

        return [
            super().clean(data, initial)
        ]


class SubirFotosGaleriaForm(forms.Form):
    """Sube varias fotos de una vez a la misma categoría de la galería."""

    categoria = forms.ChoiceField(
        label='Categoría',
        choices=FotoGaleria._meta.get_field(
            'categoria'
        ).choices,
        widget=forms.Select(
            attrs={'class': 'form-control'}
        ),
    )

    imagenes = _VariasImagenesField(
        label='Imágenes',
        help_text=(
            'Puedes seleccionar varias a la vez '
            '(Ctrl o Shift + clic).'
        ),
        error_messages={
            'required': 'Selecciona al menos una imagen.',
            'invalid_image': (
                'Uno de los archivos no es una imagen válida.'
            ),
        },
        widget=_VariosArchivosInput(
            attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }
        ),
    )


class CotizacionEstadoForm(forms.ModelForm):
    """
    Edición reducida de una cotización desde el panel:
    el admin solo gestiona el estado y sus notas internas.
    """

    class Meta:
        model = Cotizacion

        fields = [
            'estado',
            'notas_admin',
            'motivo_rechazo'
        ]

        labels = {
            'motivo_rechazo': (
                'Motivo del rechazo '
                '(se le envía al cliente)'
            )
        }

        widgets = {
            'estado': forms.Select(
                attrs={'class': 'form-control'}
            ),
            'notas_admin': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'rows': 4,
                    'placeholder': (
                        'Notas internas '
                        '(no visibles para el cliente)'
                    )
                }
            ),
            'motivo_rechazo': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'rows': 3,
                    'placeholder': (
                        'Opcional. Solo se usa si el estado '
                        'es "Rechazada".'
                    )
                }
            ),
        }


# ─────────────────────────────────────────────────────────────────────────
# Tabla de precios (panel → Precios). Ver Bd_PremiumEventos/precios.py.
# ─────────────────────────────────────────────────────────────────────────

class PaquetePrecioForm(forms.ModelForm):

    class Meta:
        model = PaquetePrecio

        fields = [
            'invitados',
            'precio'
        ]

        error_messages = {
            'invitados': {
                'unique': (
                    'Ya hay un tramo con este número de invitados.'
                )
            }
        }

        widgets = {
            'invitados': forms.NumberInput(
                attrs={
                    'class': 'form-control',
                    'min': 1,
                    'placeholder': 'Ej. 50'
                }
            ),
            'precio': forms.NumberInput(
                attrs={
                    'class': 'form-control',
                    'min': 0,
                    'step': 1000,
                    'placeholder': 'Ej. 3900000'
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.instance.pk:
            self.initial['precio'] = int(
                self.instance.precio
            )

    def clean_precio(self):
        precio = self.cleaned_data['precio']

        if precio is not None and precio <= 0:
            raise forms.ValidationError(
                'El precio debe ser mayor que cero.'
            )

        return precio


class _TablaPreciosFormSetBase(forms.BaseModelFormSet):
    """
    Revisa la tabla completa antes de guardarla:
    no se puede quedar vacía, no se pueden repetir tramos
    y el precio debe subir a medida que suben los invitados.
    """

    def get_unique_error_message(self, unique_check):
        return (
            'Hay dos filas con el mismo número de invitados.'
        )

    def clean(self):
        super().clean()

        if any(self.errors):
            return

        tramos = []

        for form in self.forms:

            if not form.has_changed() and not form.instance.pk:
                continue

            if self.can_delete and self._should_delete_form(form):
                continue

            invitados = form.cleaned_data.get('invitados')
            precio = form.cleaned_data.get('precio')

            if invitados is None or precio is None:
                raise forms.ValidationError(
                    'Cada fila debe tener número de invitados y precio.'
                )

            tramos.append(
                (invitados, precio)
            )

        if not tramos:
            raise forms.ValidationError(
                'La tabla debe tener al menos un tramo.'
            )

        cantidades = [
            inv
            for inv, _ in tramos
        ]

        repetidos = sorted({
            inv
            for inv in cantidades
            if cantidades.count(inv) > 1
        })

        if repetidos:
            raise forms.ValidationError(
                'Hay tramos repetidos: '
                + ', '.join(
                    f'{inv} invitados'
                    for inv in repetidos
                )
                + '.'
            )

        tramos.sort()

        for (inv_a, precio_a), (inv_b, precio_b) in zip(
            tramos,
            tramos[1:]
        ):

            if precio_b < precio_a:
                raise forms.ValidationError(
                    f'El precio de {inv_b} invitados '
                    f'(${precio_b:,.0f}) no puede ser menor que '
                    f'el de {inv_a} invitados '
                    f'(${precio_a:,.0f}).'
                    .replace(',', '.')
                )


TablaPreciosFormSet = forms.modelformset_factory(
    PaquetePrecio,
    form=PaquetePrecioForm,
    formset=_TablaPreciosFormSetBase,
    extra=1,
    can_delete=True,
)


class ConfiguracionPreciosForm(forms.ModelForm):

    class Meta:
        model = ConfiguracionPrecios

        fields = [
            'tarifa_invitado_adicional'
        ]

        labels = {
            'tarifa_invitado_adicional':
                'Valor por cada invitado adicional'
        }

        help_texts = {
            'tarifa_invitado_adicional':
                'Se suma por cada invitado por encima '
                'del tramo más grande de la tabla.'
        }

        widgets = {
            'tarifa_invitado_adicional': forms.NumberInput(
                attrs={
                    'class': 'form-control',
                    'min': 0,
                    'step': 1000
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.initial[
            'tarifa_invitado_adicional'
        ] = int(
            self.instance.tarifa_invitado_adicional
        )


class ServicioPrecioForm(forms.ModelForm):

    class Meta:
        model = ServicioPrecio

        fields = [
            'nombre',
            'precio',
        ]

        widgets = {
            'nombre': forms.TextInput(
                attrs={
                    'class': 'form-control',
                }
            ),
            'precio': forms.NumberInput(
                attrs={
                    'class': 'form-control',
                    'min': 0,
                    'step': 1000,
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.instance.pk:
            self.initial['precio'] = int(
                self.instance.precio
            )

    def clean_precio(self):
        precio = self.cleaned_data['precio']

        if precio is not None and precio < 0:
            raise forms.ValidationError(
                'El precio no puede ser negativo.'
            )

        return precio


# Formulario para editar todos los precios
# de servicios desde el dashboard.
ServiciosPreciosFormSet = modelformset_factory(
    ServicioPrecio,
    form=ServicioPrecioForm,
    extra=0,
)

