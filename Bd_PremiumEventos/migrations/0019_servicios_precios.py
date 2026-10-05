from decimal import Decimal

from django.db import migrations, models


SERVICIOS_INICIALES = [
    ('decoracion', 'Decoración', 'principal', '800000'),
    ('mobiliario', 'Mobiliario', 'principal', '500000'),
    ('organizacion_completa', 'Organización completa', 'principal', '700000'),
    ('miniteca', 'Miniteca', 'principal', '600000'),
    ('bar', 'Bar', 'principal', '900000'),
    ('banquete', 'Banquete', 'principal', '1200000'),
    ('alquiler', 'Alquiler', 'principal', '400000'),

    ('fotografia', 'Fotografía', 'otros', '500000'),
    ('camara_360', 'Cámara 360', 'otros', '350000'),
    ('ceremonias_privadas', 'Ceremonias privadas', 'otros', '450000'),
    ('inflables_magos_titeres', 'Inflables, magos y títeres', 'otros', '450000'),
    ('pistas_de_baile', 'Pistas de baile', 'otros', '800000'),
    ('edecanes', 'Edecanes', 'otros', '300000'),
    ('granizados', 'Granizados', 'otros', '250000'),
    ('polvora_fria', 'Pólvora fría', 'otros', '300000'),
    ('musica_en_vivo', 'Música en vivo', 'otros', '1200000'),
    ('servicio_audio_visual', 'Servicio audiovisual', 'otros', '600000'),
]


def cargar_servicios(apps, schema_editor):
    ServicioPrecio = apps.get_model(
        'Bd_PremiumEventos',
        'ServicioPrecio'
    )

    for clave, nombre, categoria, precio in SERVICIOS_INICIALES:
        ServicioPrecio.objects.get_or_create(
            clave=clave,
            defaults={
                'nombre': nombre,
                'categoria': categoria,
                'precio': Decimal(precio),
            }
        )


def borrar_servicios(apps, schema_editor):
    ServicioPrecio = apps.get_model(
        'Bd_PremiumEventos',
        'ServicioPrecio'
    )

    ServicioPrecio.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('Bd_PremiumEventos', '0018_cargar_tabla_precios'),
    ]

    operations = [
        migrations.CreateModel(
            name='ServicioPrecio',
            fields=[
                (
                    'id',
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name='ID',
                    ),
                ),
                (
                    'clave',
                    models.CharField(
                        max_length=80,
                        unique=True,
                    ),
                ),
                (
                    'nombre',
                    models.CharField(
                        max_length=150,
                    ),
                ),
                (
                    'categoria',
                    models.CharField(
                        choices=[
                            ('principal', 'Servicio que desea cotizar'),
                            ('otros', 'Otros Servicios'),
                        ],
                        default='principal',
                        max_length=20,
                    ),
                ),
                (
                    'precio',
                    models.DecimalField(
                        decimal_places=2,
                        default=0,
                        max_digits=12,
                    ),
                ),
            ],
            options={
                'db_table': 'servicio_precio',
                'ordering': ['categoria', 'nombre'],
            },
        ),
        migrations.RunPython(
            cargar_servicios,
            borrar_servicios
        ),
    ]