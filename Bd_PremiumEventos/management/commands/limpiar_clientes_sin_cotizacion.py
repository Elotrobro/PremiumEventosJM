from django.core.management.base import BaseCommand

from Bd_PremiumEventos.limpieza import DIAS_SIN_COTIZAR, clientes_vencidos, eliminar_clientes_vencidos


class Command(BaseCommand):
    help = (
        f'Elimina las cuentas de cliente que llevan más de {DIAS_SIN_COTIZAR} días creadas sin '
        'haber hecho ninguna cotización. Con --simular solo muestra cuáles serían.'
    )

    def add_arguments(self, parser):
        parser.add_argument('--simular', action='store_true', help='Solo lista las cuentas, no elimina nada.')

    def handle(self, *args, **options):
        if options['simular']:
            vencidos = list(clientes_vencidos())
            for usuario in vencidos:
                self.stdout.write(f'  - {usuario.nombre_completo} <{usuario.correo_electronico}> '
                                  f'(creado {usuario.fecha_creacion:%Y-%m-%d})')
            self.stdout.write(self.style.WARNING(f'Se eliminarían {len(vencidos)} cuenta(s).'))
            return

        total = eliminar_clientes_vencidos()
        self.stdout.write(self.style.SUCCESS(f'Se eliminaron {total} cuenta(s) de cliente sin cotizaciones.'))
