from decimal import Decimal, InvalidOperation


def formatear_miles(valor):
    """
    Formatea un número con punto como separador de miles, igual a como ya
    se hace en el mensaje de éxito de la cotización pública (ver
    Bd_PremiumEventos/views.py -> cotizacion_view). Se usa tanto en las
    plantillas del panel (filtro 'miles', ver templatetags/panel_extras.py)
    como al generar el PDF del historial, para que ambos coincidan.

    Devuelve el valor tal cual si no es un número (así una plantilla
    puede aplicar el filtro sin miedo a romper con un texto vacío o None).
    """
    if valor is None or valor == '':
        return valor
    try:
        numero = Decimal(str(valor))
    except (InvalidOperation, ValueError, TypeError):
        return valor
    return f'{numero:,.0f}'.replace(',', '.')
