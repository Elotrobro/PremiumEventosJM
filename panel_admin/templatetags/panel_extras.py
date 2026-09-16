from django import template

from panel_admin.utils import formatear_miles

register = template.Library()


@register.filter(name='miles')
def miles(valor):
    """Uso en plantilla: {{ numero|miles }} -> "1.234.567" (punto como separador)."""
    return formatear_miles(valor)
