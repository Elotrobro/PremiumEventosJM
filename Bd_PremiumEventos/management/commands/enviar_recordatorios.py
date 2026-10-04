from datetime import date

from django.core.management.base import BaseCommand, CommandError

from Bd_PremiumEventos.recordatorios import enviar_recordatorios, hoy_negocio, recordatorios_pendientes


class Command(BaseCommand):
    help = (
        'Envía por n8n los recordatorios del día: al cliente 3 días y 1 día antes de su evento, '
        'el mismo día y el día siguiente; y el resumen diario a la administradora. '
        'Pensado para correrse una vez al día (no repite los que ya se enviaron).'
    )

    def add_arguments(self, parser):
        parser.add_argument('--simular', action='store_true', help='Solo lista lo que se enviaría, no envía nada.')
        parser.add_argument('--fecha', help='Hace de cuenta que hoy es esta fecha (AAAA-MM-DD). Útil para probar.')

    def handle(self, *args, **options):
        try:
            hoy = date.fromisoformat(options['fecha']) if options['fecha'] else hoy_negocio()
        except ValueError:
            raise CommandError('La fecha debe tener el formato AAAA-MM-DD.')

        if options['simular']:
            pendientes = recordatorios_pendientes(hoy)
            for clave, datos in pendientes:
                para = datos['correo'] or 'administradora'
                self.stdout.write(f'  - {clave} → {para}: {datos["asunto"]}')
            self.stdout.write(self.style.WARNING(f'Se enviarían {len(pendientes)} recordatorio(s) ({hoy}).'))
            return

        try:
            resultado = enviar_recordatorios(hoy)
        except RuntimeError as error:
            raise CommandError(str(error))
        for clave in resultado['enviados']:
            self.stdout.write(f'  ✓ {clave}')
        for clave in resultado['fallidos']:
            self.stdout.write(self.style.ERROR(f'  ✗ {clave} (n8n no respondió, se reintenta en la próxima ejecución)'))
        self.stdout.write(self.style.SUCCESS(
            f'Enviados: {len(resultado["enviados"])} · Fallidos: {len(resultado["fallidos"])} ({hoy}).'
        ))
