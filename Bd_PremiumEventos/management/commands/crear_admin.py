import getpass

from django.contrib.auth.hashers import make_password
from django.core.management.base import BaseCommand, CommandError

from Bd_PremiumEventos.models import Usuario


class Command(BaseCommand):
    """
    Crea (o promueve a admin) un usuario en la tabla propia `usuario`,
    la que usa el login del sitio (Bd_PremiumEventos.views.login_view).

    Esto NO es un superusuario de django.contrib.auth: es independiente
    del /admin/ nativo de Django. Se ejecuta así:

        python manage.py crear_admin
        python manage.py crear_admin --correo admin@premiumeventosjm.com --nombre "Admin" --password "algo-seguro"
    """
    help = 'Crea un usuario con rol "admin" para poder entrar al panel de administrador (/panel-admin/).'

    def add_arguments(self, parser):
        parser.add_argument('--nombre', help='Nombre completo del administrador.')
        parser.add_argument('--correo', help='Correo electrónico (se usa para iniciar sesión).')
        parser.add_argument('--password', help='Contraseña. Si se omite, se pide de forma oculta por consola.')

    def handle(self, *args, **options):
        nombre = options.get('nombre') or input('Nombre completo: ').strip()
        correo = (options.get('correo') or input('Correo electrónico: ').strip()).lower()

        if not nombre or not correo:
            raise CommandError('El nombre y el correo son obligatorios.')

        password = options.get('password')
        if not password:
            password = getpass.getpass('Contraseña: ')
            password_confirm = getpass.getpass('Confirma la contraseña: ')
            if password != password_confirm:
                raise CommandError('Las contraseñas no coinciden.')

        if not password:
            raise CommandError('La contraseña no puede estar vacía.')

        usuario, creado = Usuario.objects.get_or_create(
            correo_electronico__iexact=correo,
            defaults={
                'nombre_completo': nombre,
                'correo_electronico': correo,
                'contrasena': make_password(password),
                'rol': 'admin',
            },
        )

        if not creado:
            # Ya existía un usuario con ese correo: se promueve a admin y
            # se actualiza su contraseña con la indicada.
            usuario.nombre_completo = nombre
            usuario.rol = 'admin'
            usuario.contrasena = make_password(password)
            usuario.save()
            self.stdout.write(self.style.SUCCESS(
                f'El usuario "{correo}" ya existía: se actualizó su contraseña y se promovió a rol "admin".'
            ))
        else:
            self.stdout.write(self.style.SUCCESS(
                f'Usuario administrador "{correo}" creado correctamente. Ya puedes iniciar sesión en el sitio '
                'y acceder a /panel-admin/.'
            ))
