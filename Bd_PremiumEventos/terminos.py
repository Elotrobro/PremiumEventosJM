"""
Términos y condiciones y Política de privacidad (tratamiento de datos).

Para crear una cuenta (con correo y contraseña o con Google) hay que marcar
las dos casillas del registro (base.html). Es la autorización previa,
expresa e informada que pide la Ley 1581 de 2012 (art. 9) y queda guardada
como prueba en Usuario.terminos_aceptados y Usuario.version_terminos
(art. 17 lit. b).

Los textos están en core/templates/legal/terminos.html y privacidad.html.
Si se cambian de forma importante, actualiza VERSION y FECHA_TEXTO: así se
sabe qué versión aceptó cada cuenta.
"""

VERSION = '2026-11-24'
FECHA_TEXTO = '24 de noviembre de 2026'

# Nombres de las casillas en el formulario de registro y en el de Google.
CAMPO_TERMINOS = 'acepta_terminos'
CAMPO_PRIVACIDAD = 'acepta_privacidad'

MENSAJE_FALTA_ACEPTAR = (
    'Para crear tu cuenta debes aceptar los Términos y condiciones '
    'y la Política de privacidad (tratamiento de datos personales).'
)


def acepto_todo(datos):
    """True si en el POST vienen marcadas las dos casillas."""
    return datos.get(CAMPO_TERMINOS) == 'on' and datos.get(CAMPO_PRIVACIDAD) == 'on'
