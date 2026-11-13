from django.db import migrations, models
import django.db.models.deletion

import Bd_PremiumEventos.models


# Los tres salones que estaban escritos a mano en core/templates/convenios.html,
# para que la página se vea igual que antes al pasar a la base de datos.
SALONES_INICIALES = [
    {
        'nombre': 'Salón Imperial JM',
        'ubicacion': 'Sede Principal',
        'descripcion': 'Amplio salón con iluminación arquitectónica, aire acondicionado y capacidad flexible para grandes celebraciones.',
        'capacidad': 150,
        'caracteristicas': 'Parqueadero disponible\nSonido y Luces integradas',
        'icono': 'fa-hotel',
    },
    {
        'nombre': 'Terraza Campestre',
        'ubicacion': 'Zona Sur',
        'descripcion': 'Hermoso espacio al aire libre rodeado de naturaleza, ideal para ceremonias diurnas y recepciones románticas.',
        'capacidad': 100,
        'caracteristicas': 'Zona verde y pérgolas\nExcelentes escenarios fotográficos',
        'icono': 'fa-tree',
    },
    {
        'nombre': 'Salón Lounge Ejecutiva',
        'ubicacion': 'Centro de la Ciudad',
        'descripcion': 'Ambiente moderno y sofisticado perfecto para eventos empresariales, lanzamientos de marca y cócteles exclusivos.',
        'capacidad': 80,
        'caracteristicas': 'Conectividad y proyector\nBarra de bar integrada',
        'icono': 'fa-glass-cheers',
    },
]


def cargar_salones(apps, schema_editor):
    Salon = apps.get_model('Bd_PremiumEventos', 'Salon')
    for datos in SALONES_INICIALES:
        Salon.objects.get_or_create(nombre=datos['nombre'], defaults=datos)


def quitar_salones(apps, schema_editor):
    Salon = apps.get_model('Bd_PremiumEventos', 'Salon')
    Salon.objects.filter(nombre__in=[s['nombre'] for s in SALONES_INICIALES]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('Bd_PremiumEventos', '0019_servicios_precios'),
    ]

    operations = [
        migrations.CreateModel(
            name='Salon',
            fields=[
                ('id_salon', models.AutoField(primary_key=True, serialize=False)),
                ('nombre', models.CharField(max_length=150)),
                ('ubicacion', models.CharField(help_text='Ej. Sede Principal, Zona Sur, Centro de la Ciudad.', max_length=150)),
                ('descripcion', models.TextField()),
                ('capacidad', models.PositiveIntegerField(help_text='Número máximo de personas.')),
                ('caracteristicas', models.TextField(blank=True, help_text='Una por línea. Ej.: Parqueadero disponible')),
                ('icono', models.CharField(choices=[('fa-hotel', 'Hotel / salón'), ('fa-tree', 'Campestre / al aire libre'), ('fa-glass-cheers', 'Lounge / coctel'), ('fa-building', 'Edificio / empresarial'), ('fa-church', 'Capilla / ceremonia'), ('fa-umbrella-beach', 'Piscina / playa')], default='fa-hotel', max_length=40)),
                ('activo', models.BooleanField(default=True)),
                ('fecha_creacion', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'db_table': 'salon',
                'ordering': ['id_salon'],
            },
        ),
        migrations.CreateModel(
            name='FotoSalon',
            fields=[
                ('id_foto', models.AutoField(primary_key=True, serialize=False)),
                ('imagen', models.ImageField(upload_to=Bd_PremiumEventos.models._ruta_imagen_salon)),
                ('fecha_subida', models.DateTimeField(auto_now_add=True)),
                ('salon', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='fotos', to='Bd_PremiumEventos.salon')),
            ],
            options={
                'db_table': 'foto_salon',
                'ordering': ['fecha_subida', 'id_foto'],
            },
        ),
        migrations.RunPython(cargar_salones, quitar_salones),
    ]
