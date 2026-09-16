import random
import string

from django.db import models
from django.utils import timezone

# ═══════════════════════════════════════════════════════════════════════
# Modelos de la app Bd_PremiumEventos
#
# Estos modelos representan tablas que ya existían (o se diseñaron) en
# MySQL, por eso casi todos definen `db_table` (nombre real de la tabla)
# y algunos usan `db_column` (nombre real de la columna) cuando el nombre
# en la base de datos no coincide con el nombre "pythonico" del campo.
# ═══════════════════════════════════════════════════════════════════════


class Usuario(models.Model):
    """
    Cuenta con acceso al sitio (quien puede iniciar sesión y solicitar
    cotizaciones). No usa el sistema de usuarios nativo de Django
    (django.contrib.auth.User); es una tabla propia, autenticada
    manualmente en Bd_PremiumEventos/views.py (login_view).
    """
    ROL_ADMIN = 'admin'
    ROL_EMPLEADO = 'empleado'
    ROL_CLIENTE = 'cliente'
    ROL_CHOICES = [
        (ROL_ADMIN, 'Administrador'),
        (ROL_EMPLEADO, 'Empleado'),
        (ROL_CLIENTE, 'Cliente'),
    ]

    id_usuario = models.AutoField(primary_key=True)
    nombre_completo = models.CharField(max_length=150)
    correo_electronico = models.EmailField(max_length=100, unique=True)  # único: se usa para buscar el usuario al iniciar sesión
    contrasena = models.CharField(max_length=255, db_column='contraseña')  # Evitamos la 'ñ' en el nombre de variable Python
    # Aunque ahora hay ROL_CHOICES, el campo sigue siendo texto libre a
    # nivel de base de datos (sin CHECK constraint): los choices solo
    # afectan los formularios y el admin, para no arriesgar una migración
    # que falle si por alguna razón ya existiera un valor distinto guardado.
    rol = models.CharField(max_length=50, choices=ROL_CHOICES, default=ROL_CLIENTE)
    ultimo_acceso = models.DateTimeField(null=True, blank=True)  # se actualiza cada vez que el login es exitoso (ver login_view)
    fecha_creacion = models.DateTimeField(auto_now_add=True)  # se llena automáticamente al crear el registro, no editable después

    def __str__(self):
        # Texto que se muestra en el admin y en cualquier <select> relacionado con este modelo
        return f"{self.nombre_completo} ({self.rol})"

    class Meta:
        db_table = 'usuario'  # nombre real de la tabla en MySQL


class Cliente(models.Model):
    """
    Datos de contacto de un usuario, usados para llenar cada cotización
    (nombre, correo y WhatsApp). Se crea/actualiza automáticamente la
    primera vez que un usuario envía el formulario de cotización
    (ver Cliente.objects.get_or_create en cotizacion_view).
    """
    id_cliente = models.AutoField(primary_key=True)
    nombre_completo = models.CharField(max_length=150)
    correo_electronico = models.EmailField(max_length=100)
    telefono_whatsapp = models.CharField(max_length=15)
    fecha_registro = models.DateTimeField(auto_now_add=True)
    # Relación 1 a 1 en la práctica: cada Usuario tiene como máximo un Cliente
    # asociado (get_or_create en cotizacion_view solo crea uno por usuario).
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, db_column='id_usuario')

    def __str__(self):
        return self.nombre_completo

    class Meta:
        db_table = 'cliente'


class ContactoSimple(models.Model):
    """
    Mensajes enviados desde un formulario de contacto público (sin
    necesidad de sesión iniciada).

    ⚠️ Pendiente: hoy no existe ninguna vista que guarde datos aquí.
    El formulario de contacto.html todavía no está conectado al backend
    (su <form> apunta a action="#"), por lo que esta tabla está lista
    pero sin usarse todavía.
    """
    id_contacto = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100)
    apellidos = models.CharField(max_length=100)
    email = models.EmailField(max_length=100)
    telefono = models.CharField(max_length=15)
    mensaje = models.TextField()
    fecha_contacto = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Mensaje de {self.nombre} {self.apellidos}"

    class Meta:
        db_table = 'contacto_simple'


class ItemDecoracion(models.Model):
    """
    Catálogo de artículos de alquiler/decoración (ej. sillas, manteles,
    cilindros decorativos) con su precio y si está disponible o no.

    ⚠️ Pendiente: el catálogo público (catalogo.html) todavía NO lee de
    este modelo; los productos y precios que ve el visitante están
    escritos directamente en el HTML. Este modelo solo se gestiona hoy
    desde el panel de administración de Django.
    """
    id_item = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=150)
    descripcion = models.TextField()
    precio = models.DecimalField(max_digits=12, decimal_places=2)
    estado = models.BooleanField(default=True)  # TINYINT(1) se traduce a Boolean; True = disponible para alquilar

    def __str__(self):
        return self.nombre

    class Meta:
        db_table = 'item_decoracion'


class CarritoSeleccion(models.Model):
    """
    Cabecera de un carrito de selección de ítems de decoración (uno por
    usuario, mientras esté "activo"). Pensado para persistir en base de
    datos lo que hoy el usuario arma solo en memoria del navegador
    (ver core/static/js/catalogo.js, que NO usa este modelo todavía).
    """
    id_carrito = models.AutoField(primary_key=True)
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, db_column='id_usuario')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=50, default='activo')  # ej. 'activo', 'finalizado' (texto libre, sin choices)

    def __str__(self):
        return f"Carrito #{self.id_carrito} - {self.usuario.nombre_completo}"

    class Meta:
        db_table = 'carrito_seleccion'


class DetalleCarrito(models.Model):
    """
    Línea de un carrito: qué ítem se seleccionó, en qué cantidad y a qué
    precio unitario (se guarda el precio en el momento de agregarlo, para
    no verse afectado si el precio del ítem cambia después).
    """
    id_detalle_carrito = models.AutoField(primary_key=True)
    carrito = models.ForeignKey(CarritoSeleccion, on_delete=models.CASCADE, db_column='id_carrito')
    item = models.ForeignKey(ItemDecoracion, on_delete=models.CASCADE, db_column='id_item')
    cantidad = models.IntegerField(default=1)
    precio_unitario = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return f"{self.cantidad}x {self.item.nombre}"

    class Meta:
        db_table = 'detalle_carrito'


def generar_codigo_seguimiento():
    """
    Genera un código de seguimiento al estilo de los que usan las
    empresas de envíos para rastrear un paquete (ej. "PJM-20260916-8K3QZF"):
    prefijo de la empresa + fecha + 6 caracteres al azar. No se basa en el
    id_cotizacion a propósito, para que no sea adivinable ni revele cuántas
    cotizaciones existen en total con solo mirar el código.
    """
    fecha = timezone.localdate().strftime('%Y%m%d')
    sufijo = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f'PJM-{fecha}-{sufijo}'


class Cotizacion(models.Model):
    """
    Solicitud de cotización de un evento, generada desde el formulario
    modal de inicio.html y procesada por cotizacion_view.

    nombre_cliente / correo_cliente / telefono_cliente quedan duplicados
    respecto a los datos que ya tiene `cliente` (ForeignKey) a propósito:
    así queda registrado exactamente lo que la persona escribió en ESE
    formulario, aunque después actualice sus datos de contacto generales.
    """
    id_cotizacion = models.AutoField(primary_key=True)
    # Código único para que el cliente y el administrador puedan hacer
    # seguimiento a la cotización (ver generar_codigo_seguimiento y el
    # save() de abajo). blank=True porque se autogenera en el primer
    # guardado; nunca queda vacío en la práctica.
    codigo_seguimiento = models.CharField(max_length=30, unique=True, blank=True)
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, db_column='id_cliente')
    nombre_cliente = models.CharField(max_length=150)
    correo_cliente = models.EmailField(max_length=100)
    telefono_cliente = models.CharField(max_length=15)
    fecha_evento = models.DateField()
    cantidad_invitados = models.IntegerField()
    tema_estilo = models.CharField(max_length=100)
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()  # calculada automáticamente en el backend: hora_inicio + 4 horas (ver cotizacion_view)
    ubicacion = models.CharField(max_length=100)

    ESTADO_PENDIENTE = 'pendiente'
    ESTADO_APROBADA = 'aprobada'
    ESTADO_RECHAZADA = 'rechazada'
    ESTADO_COMPLETADA = 'completada'
    ESTADO_PAGADO = 'pagado'
    ESTADO_CHOICES = [
        (ESTADO_PENDIENTE, 'Pendiente'),
        (ESTADO_APROBADA, 'Aprobada'),
        (ESTADO_RECHAZADA, 'Rechazada'),
        (ESTADO_COMPLETADA, 'Completada'),
        (ESTADO_PAGADO, 'Pagado'),
    ]
    # Estado de gestión de la cotización dentro del panel de administrador
    # (no lo llena el cliente; lo cambia el admin al revisar la solicitud).
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default=ESTADO_PENDIENTE)
    # Notas internas del administrador sobre esta cotización (no se muestran al cliente).
    notas_admin = models.TextField(blank=True, default='')

    def save(self, *args, **kwargs):
        # Se genera el código de seguimiento antes del primer guardado
        # (nunca se reemplaza uno que ya exista). Se comprueba que no
        # choque con uno ya guardado; con 6 caracteres al azar la
        # probabilidad de choque es mínima, pero el bucle es la única
        # forma de *garantizar* que quede único.
        if not self.codigo_seguimiento:
            codigo = generar_codigo_seguimiento()
            while Cotizacion.objects.filter(codigo_seguimiento=codigo).exists():
                codigo = generar_codigo_seguimiento()
            self.codigo_seguimiento = codigo
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Cotización #{self.id_cotizacion} - {self.cliente.nombre_completo}"

    class Meta:
        db_table = 'cotizacion'


class DetalleCotizacion(models.Model):
    """
    Datos adicionales de una cotización que no caben directamente en
    Cotizacion: presupuesto declarado por el cliente, precio calculado
    por el sistema (según la tabla de paquetes por invitados) y un
    resumen en JSON con los servicios seleccionados y observaciones.
    """
    id_detalle = models.AutoField(primary_key=True)
    cotizacion = models.ForeignKey(Cotizacion, on_delete=models.CASCADE, db_column='id_cotizacion')
    cantidad_personas_aplica = models.IntegerField()
    salon = models.BooleanField(default=False)  # True = el cliente ya cuenta con salón propio
    detalles = models.TextField()  # JSON con: servicios_solicitados, desea_sugerencias_sede, observaciones, etc. (ver json.dumps en cotizacion_view)
    evento = models.CharField(max_length=50)  # tipo de evento (15 años, matrimonio, grado, etc.)
    presupuesto = models.DecimalField(max_digits=12, decimal_places=2)  # lo que el cliente dijo que puede pagar (dato informativo)
    precio_cotizado = models.DecimalField(max_digits=12, decimal_places=2)  # lo que el sistema calculó automáticamente (calcular_precio_estimado)
    fecha_cotizacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Detalle de Cotización #{self.cotizacion.id_cotizacion}"

    class Meta:
        db_table = 'detalle_cotizacion'
