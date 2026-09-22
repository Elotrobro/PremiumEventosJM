"""
Recuperación de contraseña, en 4 pasos (mismo flujo que las vistas
PasswordReset* de Django, pero sobre la tabla propia `usuario`, porque
este sitio no usa django.contrib.auth.User):

  1. recuperar_password         → el usuario escribe su correo y se le envía un enlace.
  2. recuperar_password_enviado → "revisa tu correo".
  3. restablecer_password       → el enlace del correo lleva aquí; escribe la contraseña nueva.
  4. recuperar_password_completo → "tu contraseña fue cambiada".
"""

from django.contrib.auth.hashers import make_password
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.core.mail import send_mail
from django.shortcuts import redirect, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode

from .models import Usuario


class TokenRecuperacion(PasswordResetTokenGenerator):
    """
    El generador de Django espera un User (password, last_login, email);
    aquí se le pasan los campos equivalentes de Usuario. Como el hash de la
    contraseña forma parte del token, el enlace deja de servir en cuanto la
    contraseña se cambia: cada enlace se puede usar una sola vez.
    """
    def _make_hash_value(self, usuario, timestamp):
        ultimo_acceso = '' if usuario.ultimo_acceso is None else usuario.ultimo_acceso.replace(microsecond=0, tzinfo=None)
        return f'{usuario.pk}{usuario.contrasena}{ultimo_acceso}{timestamp}{usuario.correo_electronico}'


token_recuperacion = TokenRecuperacion()


def recuperar_password(request):
    if request.method == 'POST':
        correo = request.POST.get('correo_electronico', '').strip().lower()
        usuario = Usuario.objects.filter(correo_electronico__iexact=correo).first()

        if usuario is not None:
            uid = urlsafe_base64_encode(force_bytes(usuario.pk))
            token = token_recuperacion.make_token(usuario)
            enlace = request.build_absolute_uri(reverse('password_reset_confirm', args=[uid, token]))
            contexto = {'usuario': usuario, 'enlace': enlace}

            asunto = render_to_string('recuperacion/password_reset_subject.txt', contexto).strip()
            cuerpo = render_to_string('recuperacion/password_reset_email.txt', contexto)
            send_mail(asunto, cuerpo, None, [usuario.correo_electronico])

        # Se redirige igual exista o no el correo, para no revelar qué
        # correos están registrados en el sitio.
        return redirect('password_reset_done')

    return render(request, 'recuperacion/password_reset_form.html')


def recuperar_password_enviado(request):
    return render(request, 'recuperacion/password_reset_done.html')


def restablecer_password(request, uidb64, token):
    try:
        usuario = Usuario.objects.get(pk=force_str(urlsafe_base64_decode(uidb64)))
    except (TypeError, ValueError, OverflowError, Usuario.DoesNotExist):
        usuario = None

    enlace_valido = usuario is not None and token_recuperacion.check_token(usuario, token)
    errores = []

    if enlace_valido and request.method == 'POST':
        nueva = request.POST.get('new_password1', '')
        confirmacion = request.POST.get('new_password2', '')

        # Mismas reglas que al crear la cuenta (ver registro_view).
        if len(nueva) < 8:
            errores.append('La contraseña debe tener al menos 8 caracteres.')
        if nueva != confirmacion:
            errores.append('Las contraseñas no coinciden.')

        if not errores:
            usuario.contrasena = make_password(nueva)
            usuario.save(update_fields=['contrasena'])
            return redirect('password_reset_complete')

    return render(request, 'recuperacion/password_reset_confirm.html', {
        'validlink': enlace_valido,
        'errores': errores,
    })


def recuperar_password_completo(request):
    return render(request, 'recuperacion/password_reset_complete.html')
