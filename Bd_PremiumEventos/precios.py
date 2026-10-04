"""
Cálculo del precio estimado de un evento según el número de invitados.

La tabla vive en la base de datos (PaquetePrecio + ConfiguracionPrecios)
y la edita la administradora en el panel (panel_admin → Precios). Es la
única fuente: de aquí salen el precio que se guarda en cada cotización
(cotizacion_view), el estimado en vivo del formulario (modal.js recibe la
tabla con tabla_para_js) y los valores que usa el chatbot.

Reglas:
  - Si el número coincide con un tramo, se usa el precio de ese tramo.
  - Entre dos tramos se interpola en línea recta y se redondea a miles.
  - Por debajo del primer tramo se cobra el primer tramo (paquete mínimo).
  - Por encima del último tramo se suma la tarifa por invitado adicional.
"""

from decimal import ROUND_HALF_UP, Decimal

from .models import ConfiguracionPrecios, PaquetePrecio


def tabla_precios():
    """[(invitados, precio), ...] ordenada, y la tarifa por invitado adicional."""
    tabla = list(PaquetePrecio.objects.order_by('invitados').values_list('invitados', 'precio'))
    return tabla, ConfiguracionPrecios.actual().tarifa_invitado_adicional


def calcular_precio_estimado(cantidad_invitados, tabla=None, tarifa=None):
    """
    Precio estimado para `cantidad_invitados`. Se le puede pasar la tabla
    ya leída (tabla, tarifa) para no consultar la base de datos varias
    veces seguidas. Devuelve Decimal('0') si no hay invitados o la tabla
    está vacía.
    """
    if tabla is None:
        tabla, tarifa = tabla_precios()
    n = cantidad_invitados
    if not n or n <= 0 or not tabla:
        return Decimal('0')

    primero_inv, primero_precio = tabla[0]
    ultimo_inv, ultimo_precio = tabla[-1]

    if n <= primero_inv:
        return primero_precio

    if n >= ultimo_inv:
        return ultimo_precio + (n - ultimo_inv) * tarifa

    for (inv_inferior, precio_inferior), (inv_superior, precio_superior) in zip(tabla, tabla[1:]):
        if inv_inferior < n <= inv_superior:
            proporcion = Decimal(n - inv_inferior) / Decimal(inv_superior - inv_inferior)
            precio = precio_inferior + proporcion * (precio_superior - precio_inferior)
            # redondeo a miles (HALF_UP, igual que Math.round en modal.js)
            return (precio / 1000).quantize(Decimal('1'), rounding=ROUND_HALF_UP) * 1000

    return Decimal('0')


def tabla_para_js():
    """La tabla en el formato que espera modal.js (se pasa con json_script)."""
    tabla, tarifa = tabla_precios()
    return {
        'paquetes': [{'invitados': inv, 'precio': int(precio)} for inv, precio in tabla],
        'tarifa_adicional': int(tarifa),
    }
