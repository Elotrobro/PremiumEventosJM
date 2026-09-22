import io
import json
from datetime import date, datetime, time, timedelta
from decimal import Decimal

from django.contrib.auth.hashers import make_password
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.db import transaction

from Bd_PremiumEventos.models import (
    CarritoSeleccion, Cliente, ContactoSimple, Cotizacion, DetalleCarrito,
    DetalleCotizacion, FotoGaleria, ItemDecoracion, Testimonio, Usuario,
)
from Bd_PremiumEventos.views import calcular_precio_estimado

# Contraseña compartida por las 15 cuentas de prueba (cumple el mínimo de
# 8 caracteres de registro_view). Se hashea igual que cualquier cuenta
# real; nunca se guarda en texto plano.
CONTRASENA_PRUEBA = 'Prueba2026'

# ─────────────────────────────────────────────────────────────────────────
# 15 "clientes" de prueba. Son la base de Usuario/Cliente/Cotizacion/
# DetalleCotizacion/CarritoSeleccion/Testimonio: cada uno de estos 15
# genera exactamente una fila en cada una de esas tablas, tal como pasaría
# si esa persona se registrara, agregara algo al carrito, cotizara un
# evento y dejara una reseña.
#
# A propósito NO se generan cuentas de prueba con rol admin/empleado: esas
# cuentas dan acceso al panel de administrador, así que se crean aparte
# con `python manage.py crear_admin` (ver ese comando), no como datos de
# relleno.
# ─────────────────────────────────────────────────────────────────────────
CLIENTES = [
    {'nombre': 'Camila Restrepo Gómez', 'correo': 'camila.restrepo@prueba.com'},
    {'nombre': 'Andrés Felipe Muñoz', 'correo': 'andres.munoz@prueba.com'},
    {'nombre': 'Valentina Zuluaga Ríos', 'correo': 'valentina.zuluaga@prueba.com'},
    {'nombre': 'Santiago Correa Uribe', 'correo': 'santiago.correa@prueba.com'},
    {'nombre': 'Mariana Londoño Patiño', 'correo': 'mariana.londono@prueba.com'},
    {'nombre': 'Juan Pablo Escobar Toro', 'correo': 'juanpablo.escobar@prueba.com'},
    {'nombre': 'Isabella Vélez Cardona', 'correo': 'isabella.velez@prueba.com'},
    {'nombre': 'Sebastián Ramírez Duque', 'correo': 'sebastian.ramirez@prueba.com'},
    {'nombre': 'Daniela Ospina Betancur', 'correo': 'daniela.ospina@prueba.com'},
    {'nombre': 'Nicolás Arango Gaviria', 'correo': 'nicolas.arango@prueba.com'},
    {'nombre': 'Laura Sofía Jiménez Vargas', 'correo': 'laura.jimenez@prueba.com'},
    {'nombre': 'Miguel Ángel Herrera Soto', 'correo': 'miguel.herrera@prueba.com'},
    {'nombre': 'Paula Andrea Gómez Mesa', 'correo': 'paula.gomez@prueba.com'},
    {'nombre': 'Carlos Eduardo Marín Rojas', 'correo': 'carlos.marin@prueba.com'},
    {'nombre': 'Sara Milena Quintero Bran', 'correo': 'sara.quintero@prueba.com'},
]

# Una cotización por cliente (mismo orden que CLIENTES). `dias` es relativo
# a hoy (negativo = evento que ya pasó, para poder marcarlo completada/pagado).
COTIZACIONES = [
    {'tipo': 'matrimonio', 'tema': 'Elegante y romántico', 'invitados': 150, 'ubicacion': 'El Poblado, Medellín', 'dias': 45, 'hora': '16:00', 'estado': 'aprobada', 'salon': False},
    {'tipo': '15 años', 'tema': 'Vintage rosa', 'invitados': 80, 'ubicacion': 'Envigado', 'dias': 20, 'hora': '15:00', 'estado': 'pendiente', 'salon': True},
    {'tipo': 'grado', 'tema': 'Moderno minimalista', 'invitados': 60, 'ubicacion': 'Laureles, Medellín', 'dias': 10, 'hora': '18:00', 'estado': 'pendiente', 'salon': False},
    {'tipo': 'cumpleaños', 'tema': 'Tropical', 'invitados': 40, 'ubicacion': 'Sabaneta', 'dias': 5, 'hora': '14:00', 'estado': 'aprobada', 'salon': True},
    {'tipo': 'empresarial', 'tema': 'Corporativo elegante', 'invitados': 200, 'ubicacion': 'Rionegro', 'dias': 60, 'hora': '19:00', 'estado': 'pendiente', 'salon': False},
    {'tipo': 'matrimonio', 'tema': 'Bohemio de jardín', 'invitados': 120, 'ubicacion': 'Itagüí', 'dias': 90, 'hora': '17:00', 'estado': 'aprobada', 'salon': False},
    {'tipo': '15 años', 'tema': 'Clásico dorado', 'invitados': 100, 'ubicacion': 'Bello', 'dias': 30, 'hora': '16:00', 'estado': 'rechazada', 'salon': True},
    {'tipo': 'grado', 'tema': 'Rústico', 'invitados': 50, 'ubicacion': 'La Estrella', 'dias': 15, 'hora': '19:00', 'estado': 'pendiente', 'salon': False},
    {'tipo': 'cumpleaños', 'tema': 'Infantil superhéroes', 'invitados': 30, 'ubicacion': 'Caldas, Antioquia', 'dias': -10, 'hora': '15:00', 'estado': 'completada', 'salon': True},
    {'tipo': 'empresarial', 'tema': 'Fin de año', 'invitados': 180, 'ubicacion': 'Medellín, Centro', 'dias': -20, 'hora': '20:00', 'estado': 'pagado', 'salon': False},
    {'tipo': 'matrimonio', 'tema': 'Playero', 'invitados': 90, 'ubicacion': 'Guatapé', 'dias': 75, 'hora': '16:30', 'estado': 'pendiente', 'salon': False},
    {'tipo': '15 años', 'tema': 'Princesa', 'invitados': 70, 'ubicacion': 'Envigado', 'dias': -5, 'hora': '15:30', 'estado': 'completada', 'salon': True},
    {'tipo': 'grado', 'tema': 'Elegante', 'invitados': 45, 'ubicacion': 'Sabaneta', 'dias': 25, 'hora': '18:30', 'estado': 'rechazada', 'salon': False},
    {'tipo': 'otro', 'tema': 'Bautizo sobrio', 'invitados': 35, 'ubicacion': 'Laureles, Medellín', 'dias': -30, 'hora': '12:00', 'estado': 'pagado', 'salon': True},
    {'tipo': 'cumpleaños', 'tema': 'Retro años 80', 'invitados': 55, 'ubicacion': 'Itagüí', 'dias': 40, 'hora': '20:00', 'estado': 'aprobada', 'salon': False},
]

SERVICIOS_POR_TIPO = {
    'matrimonio': ['decoracion', 'banquete', 'musica_en_vivo', 'fotografia'],
    '15 años': ['decoracion', 'miniteca', 'pistas_de_baile', 'camara_360'],
    'grado': ['decoracion', 'bar', 'fotografia'],
    'cumpleaños': ['decoracion', 'inflables_magos_titeres', 'granizados'],
    'empresarial': ['organizacion_completa', 'servicio_audio_visual', 'banquete'],
    'otro': ['decoracion', 'mobiliario'],
}

ITEMS_DECORACION = [
    {'nombre': 'Silla Tiffany dorada', 'descripcion': 'Silla Tiffany en acabado dorado, ideal para matrimonios y 15 años.', 'precio': Decimal('8500'), 'estado': True},
    {'nombre': 'Silla Tiffany blanca', 'descripcion': 'Silla Tiffany en acabado blanco, combina con cualquier decoración.', 'precio': Decimal('8000'), 'estado': True},
    {'nombre': 'Mantel redondo blanco', 'descripcion': 'Mantel redondo para mesa de 1.5m, tela blanca premium.', 'precio': Decimal('25000'), 'estado': True},
    {'nombre': 'Mantel rectangular vino tinto', 'descripcion': 'Mantel rectangular color vino tinto para mesas alargadas.', 'precio': Decimal('30000'), 'estado': True},
    {'nombre': 'Centro de mesa floral', 'descripcion': 'Arreglo floral artificial para centro de mesa, varios colores.', 'precio': Decimal('45000'), 'estado': True},
    {'nombre': 'Candelabro de cristal', 'descripcion': 'Candelabro de cristal de 5 brazos para mesa principal.', 'precio': Decimal('60000'), 'estado': True},
    {'nombre': 'Arco de globos metálicos', 'descripcion': 'Arco decorativo de globos en tonos metálicos, 3 metros.', 'precio': Decimal('180000'), 'estado': True},
    {'nombre': 'Cortina de luces LED (10m)', 'descripcion': 'Cortina de luces LED cálidas, 10 metros, para fondo o entrada.', 'precio': Decimal('35000'), 'estado': True},
    {'nombre': 'Pista de baile iluminada 4x4', 'descripcion': 'Pista de baile modular con iluminación LED, 4x4 metros.', 'precio': Decimal('450000'), 'estado': True},
    {'nombre': 'Trono decorativo dorado', 'descripcion': 'Trono decorativo dorado para quinceañeras o cumpleaños.', 'precio': Decimal('150000'), 'estado': False},
    {'nombre': 'Cilindro decorativo espejado', 'descripcion': 'Cilindro espejado de 1m de alto, ideal para centros de mesa altos.', 'precio': Decimal('40000'), 'estado': True},
    {'nombre': 'Camino de mesa dorado', 'descripcion': 'Camino de mesa en tela dorada, 3 metros.', 'precio': Decimal('15000'), 'estado': True},
    {'nombre': 'Photo booth con accesorios', 'descripcion': 'Cabina de fotos con fondo y accesorios temáticos.', 'precio': Decimal('220000'), 'estado': True},
    {'nombre': 'Carpa/toldo 6x6', 'descripcion': 'Carpa blanca de 6x6 metros para eventos al aire libre.', 'precio': Decimal('380000'), 'estado': True},
    {'nombre': 'Barra de bar móvil', 'descripcion': 'Barra de bar móvil de madera, incluye iluminación interna.', 'precio': Decimal('320000'), 'estado': False},
]

CONTACTOS = [
    {'nombre': 'Luisa', 'apellidos': 'Ramírez Ortiz', 'email': 'luisa.ramirez@correo.com', 'telefono': '3101112201', 'mensaje': '¿Manejan paquetes para matrimonios de más de 200 invitados?'},
    {'nombre': 'Jorge', 'apellidos': 'Tabares León', 'email': 'jorge.tabares@correo.com', 'telefono': '3101112202', 'mensaje': 'Quisiera saber si tienen disponibilidad para un evento el próximo mes.'},
    {'nombre': 'Katherine', 'apellidos': 'Salazar Peña', 'email': 'katherine.salazar@correo.com', 'telefono': '3101112203', 'mensaje': '¿Hacen envíos de mobiliario fuera de Medellín?'},
    {'nombre': 'Felipe', 'apellidos': 'Cardona Ruiz', 'email': 'felipe.cardona@correo.com', 'telefono': '3101112204', 'mensaje': 'Necesito cotizar decoración para una fiesta infantil de 30 niños.'},
    {'nombre': 'Natalia', 'apellidos': 'Giraldo Mesa', 'email': 'natalia.giraldo@correo.com', 'telefono': '3101112205', 'mensaje': '¿Cuál es el tiempo mínimo de anticipación para reservar?'},
    {'nombre': 'Ricardo', 'apellidos': 'Pineda Vélez', 'email': 'ricardo.pineda@correo.com', 'telefono': '3101112206', 'mensaje': 'Vi la galería y me encantó la decoración de bautizo, ¿tienen más fotos?'},
    {'nombre': 'Alejandra', 'apellidos': 'Botero Castaño', 'email': 'alejandra.botero@correo.com', 'telefono': '3101112207', 'mensaje': 'Quiero información sobre el alquiler de sillas Tiffany por separado.'},
    {'nombre': 'Diego', 'apellidos': 'Montoya Zapata', 'email': 'diego.montoya@correo.com', 'telefono': '3101112208', 'mensaje': '¿Ofrecen servicio de fotografía sin el paquete completo de decoración?'},
    {'nombre': 'Verónica', 'apellidos': 'Aristizábal Cano', 'email': 'veronica.aristizabal@correo.com', 'telefono': '3101112209', 'mensaje': 'Me gustaría agendar una llamada para hablar sobre mi matrimonio.'},
    {'nombre': 'Esteban', 'apellidos': 'Vargas Higuita', 'email': 'esteban.vargas@correo.com', 'telefono': '3101112210', 'mensaje': '¿Trabajan con salones de eventos en Rionegro o solo en Medellín?'},
    {'nombre': 'Manuela', 'apellidos': 'Sánchez Duque', 'email': 'manuela.sanchez@correo.com', 'telefono': '3101112211', 'mensaje': 'Tengo dudas sobre las formas de pago, ¿reciben transferencia?'},
    {'nombre': 'Andrés', 'apellidos': 'Ochoa Restrepo', 'email': 'andres.ochoa@correo.com', 'telefono': '3101112212', 'mensaje': '¿Cuánto cuesta el paquete básico para 50 personas?'},
    {'nombre': 'Camila', 'apellidos': 'Franco Gil', 'email': 'camila.franco@correo.com', 'telefono': '3101112213', 'mensaje': 'Quiero saber si incluyen menú vegetariano en el servicio de banquete.'},
    {'nombre': 'Julián', 'apellidos': 'Palacio Arboleda', 'email': 'julian.palacio@correo.com', 'telefono': '3101112214', 'mensaje': '¿Puedo ver el mobiliario en persona antes de contratar?'},
    {'nombre': 'Tatiana', 'apellidos': 'Márquez Osorio', 'email': 'tatiana.marquez@correo.com', 'telefono': '3101112215', 'mensaje': 'Necesito una cotización urgente para un evento empresarial en 2 semanas.'},
]

# 15 fotos repartidas entre las 11 categorías de la galería (algunas
# categorías quedan con 2, para llegar a 15 en total). Son imágenes de
# relleno generadas en el momento (un rectángulo de color), no fotos
# reales: sirven para probar que la galería y el panel admin funcionan
# con datos en la tabla, no para publicar en el sitio.
FOTOS_GALERIA = [
    ('matrimonio', (193, 123, 60)), ('matrimonio', (168, 99, 43)),
    ('15-anos', (214, 139, 71)), ('15-anos', (233, 196, 158)),
    ('grados', (44, 42, 41)),
    ('primera-comunion', (245, 237, 228)),
    ('bautizo', (122, 104, 86)),
    ('fiesta-infantil', (255, 193, 7)),
    ('cumpleanos', (220, 53, 69)),
    ('baby-shower', (173, 216, 230)),
    ('revelacion-de-genero', (255, 105, 180)),
    ('fiesta-empresarial', (52, 58, 64)), ('fiesta-empresarial', (108, 117, 125)),
    ('alquiler-de-mobiliario', (161, 136, 127)), ('alquiler-de-mobiliario', (121, 85, 72)),
]

TESTIMONIOS = [
    {'calificacion': 5, 'comentario': 'Todo estuvo perfecto, la decoración superó lo que imaginábamos. ¡Gracias equipo!'},
    {'calificacion': 4, 'comentario': 'Muy buen servicio, llegaron puntuales y el montaje quedó impecable.'},
    {'calificacion': 5, 'comentario': 'Organizaron todo mi matrimonio y no tuve que preocuparme por nada. Excelente.'},
    {'calificacion': 3, 'comentario': 'El montaje quedó bien pero llegaron un poco tarde el día del evento.'},
    {'calificacion': 5, 'comentario': 'La fiesta de 15 años de mi hija quedó espectacular, superó nuestras expectativas.'},
    {'calificacion': 4, 'comentario': 'Buena atención y precios justos. Repetiría sin duda.'},
    {'calificacion': 2, 'comentario': 'La decoración no fue exactamente como la acordamos, esperaba más detalles.'},
    {'calificacion': 5, 'comentario': 'Excelente equipo de trabajo, muy profesionales y atentos a cada detalle.'},
    {'calificacion': 5, 'comentario': 'El evento empresarial quedó muy elegante, varios compañeros preguntaron quién lo organizó.'},
    {'calificacion': 4, 'comentario': 'Muy conformes con el resultado, aunque la comunicación pudo ser más ágil.'},
    {'calificacion': 5, 'comentario': 'El bautizo de mi bebé quedó hermoso, con detalles muy tiernos y bien pensados.'},
    {'calificacion': 4, 'comentario': 'Buen servicio en general, el mobiliario estaba en muy buen estado.'},
    {'calificacion': 5, 'comentario': 'La mejor decisión que tomamos para el grado de mi hijo, quedamos encantados.'},
    {'calificacion': 3, 'comentario': 'Cumplieron con lo básico, pero esperaba un poco más de creatividad.'},
    {'calificacion': 5, 'comentario': 'Recomendados al 100%, la revelación de género quedó tal cual la soñamos.'},
]


def _imagen_de_prueba(color):
    """Genera un PNG sólido pequeño en memoria (no depende de archivos
    externos), solo para que FotoGaleria.imagen tenga un archivo real."""
    from PIL import Image
    buffer = io.BytesIO()
    Image.new('RGB', (600, 400), color=color).save(buffer, format='PNG')
    return buffer.getvalue()


class Command(BaseCommand):
    help = 'Llena cada tabla del proyecto con 15 filas de datos de prueba (ver Bd_PremiumEventos/management/commands/seed_datos_prueba.py para el detalle exacto).'

    def handle(self, *args, **options):
        with transaction.atomic():
            usuarios = self._crear_usuarios()
            clientes = self._crear_clientes(usuarios)
            cotizaciones = self._crear_cotizaciones(clientes)
            self._crear_detalle_cotizaciones(cotizaciones)
            items = self._crear_items_decoracion()
            carritos = self._crear_carritos(usuarios)
            self._crear_detalle_carritos(carritos, items)
            self._crear_contactos()
            self._crear_fotos_galeria()
            self._crear_testimonios(usuarios)

        self.stdout.write(self.style.SUCCESS(
            'Listo: 15 filas de prueba en cada una de las 10 tablas (usuario, cliente, cotizacion, '
            'detalle_cotizacion, item_decoracion, carrito_seleccion, detalle_carrito, contacto_simple, '
            'foto_galeria y testimonio). Es seguro volver a correrlo: no duplica lo que ya existía.'
        ))

    def _crear_usuarios(self):
        contrasena_hash = make_password(CONTRASENA_PRUEBA)
        usuarios = []
        for dato in CLIENTES:
            usuario, _creado = Usuario.objects.get_or_create(
                correo_electronico=dato['correo'],
                defaults={
                    'nombre_completo': dato['nombre'],
                    'contrasena': contrasena_hash,
                    'rol': Usuario.ROL_CLIENTE,
                },
            )
            usuarios.append(usuario)
        self.stdout.write(f'  usuario: {len(usuarios)} filas')
        return usuarios

    def _crear_clientes(self, usuarios):
        clientes = []
        for i, usuario in enumerate(usuarios):
            telefono = f'300{1000000 + i:07d}'
            cliente, _creado = Cliente.objects.get_or_create(
                usuario=usuario,
                defaults={
                    'nombre_completo': usuario.nombre_completo,
                    'correo_electronico': usuario.correo_electronico,
                    'telefono_whatsapp': telefono,
                },
            )
            clientes.append(cliente)
        self.stdout.write(f'  cliente: {len(clientes)} filas')
        return clientes

    def _crear_cotizaciones(self, clientes):
        cotizaciones = []
        hoy = date.today()
        for cliente, datos in zip(clientes, COTIZACIONES):
            fecha_evento = hoy + timedelta(days=datos['dias'])
            hora_inicio = datetime.strptime(datos['hora'], '%H:%M').time()
            hora_fin = (datetime.combine(fecha_evento, hora_inicio) + timedelta(hours=4)).time()

            cotizacion, creada = Cotizacion.objects.get_or_create(
                cliente=cliente,
                fecha_evento=fecha_evento,
                defaults={
                    'nombre_cliente': cliente.nombre_completo,
                    'correo_cliente': cliente.correo_electronico,
                    'telefono_cliente': cliente.telefono_whatsapp,
                    'cantidad_invitados': datos['invitados'],
                    'tema_estilo': datos['tema'],
                    'hora_inicio': hora_inicio,
                    'hora_fin': hora_fin,
                    'ubicacion': datos['ubicacion'],
                    'estado': datos['estado'],
                },
            )
            cotizaciones.append((cotizacion, datos, creada))
        self.stdout.write(f'  cotizacion: {len(cotizaciones)} filas')
        return cotizaciones

    def _crear_detalle_cotizaciones(self, cotizaciones):
        total = 0
        for cotizacion, datos, creada in cotizaciones:
            if not creada and cotizacion.detallecotizacion_set.exists():
                total += 1
                continue
            precio = calcular_precio_estimado(datos['invitados'])
            detalles_extra = {
                'servicios_solicitados': SERVICIOS_POR_TIPO.get(datos['tipo'], ['decoracion']),
                'desea_sugerencias_sede': 'si' if datos['salon'] else 'no',
                'observaciones': 'Dato de prueba generado por seed_datos_prueba.',
                'hora_fin_estimada': 'Calculada automáticamente (+4h desde la hora de inicio)',
            }
            DetalleCotizacion.objects.create(
                cotizacion=cotizacion,
                cantidad_personas_aplica=datos['invitados'],
                salon=datos['salon'],
                detalles=json.dumps(detalles_extra, ensure_ascii=False),
                evento=datos['tipo'],
                presupuesto=precio,
                precio_cotizado=precio,
            )
            total += 1
        self.stdout.write(f'  detalle_cotizacion: {total} filas')

    def _crear_items_decoracion(self):
        items = []
        for dato in ITEMS_DECORACION:
            item, _creado = ItemDecoracion.objects.get_or_create(
                nombre=dato['nombre'],
                defaults={
                    'descripcion': dato['descripcion'],
                    'precio': dato['precio'],
                    'estado': dato['estado'],
                },
            )
            items.append(item)
        self.stdout.write(f'  item_decoracion: {len(items)} filas')
        return items

    def _crear_carritos(self, usuarios):
        carritos = []
        for i, usuario in enumerate(usuarios):
            estado = 'activo' if i % 3 != 0 else 'finalizado'
            carrito, _creado = CarritoSeleccion.objects.get_or_create(
                usuario=usuario,
                defaults={'estado': estado},
            )
            carritos.append(carrito)
        self.stdout.write(f'  carrito_seleccion: {len(carritos)} filas')
        return carritos

    def _crear_detalle_carritos(self, carritos, items):
        total = 0
        for i, carrito in enumerate(carritos):
            if DetalleCarrito.objects.filter(carrito=carrito).exists():
                total += 1
                continue
            item = items[i % len(items)]
            cantidad = (i % 6) + 1
            DetalleCarrito.objects.create(
                carrito=carrito,
                item=item,
                cantidad=cantidad,
                precio_unitario=item.precio,
            )
            total += 1
        self.stdout.write(f'  detalle_carrito: {total} filas')

    def _crear_contactos(self):
        total = 0
        for dato in CONTACTOS:
            _obj, creado = ContactoSimple.objects.get_or_create(
                email=dato['email'],
                defaults={
                    'nombre': dato['nombre'],
                    'apellidos': dato['apellidos'],
                    'telefono': dato['telefono'],
                    'mensaje': dato['mensaje'],
                },
            )
            total += 1
        self.stdout.write(f'  contacto_simple: {total} filas')

    def _crear_fotos_galeria(self):
        total = 0
        for i, (categoria, color) in enumerate(FOTOS_GALERIA, start=1):
            nombre_archivo = f'prueba_{i:02d}.png'
            if FotoGaleria.objects.filter(categoria=categoria, imagen__endswith=nombre_archivo).exists():
                total += 1
                continue
            foto = FotoGaleria(categoria=categoria)
            foto.imagen.save(nombre_archivo, ContentFile(_imagen_de_prueba(color)), save=True)
            total += 1
        self.stdout.write(f'  foto_galeria: {total} filas')

    def _crear_testimonios(self, usuarios):
        total = 0
        for i, (usuario, dato) in enumerate(zip(usuarios, TESTIMONIOS)):
            if Testimonio.objects.filter(usuario=usuario).exists():
                total += 1
                continue
            Testimonio.objects.create(
                usuario=usuario,
                calificacion=dato['calificacion'],
                comentario=dato['comentario'],
                aprobado=(i % 3 != 0),  # 10 aprobados, 5 pendientes de aprobar
                activo=True,
            )
            total += 1
        self.stdout.write(f'  testimonio: {total} filas')
