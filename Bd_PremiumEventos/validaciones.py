"""
Reglas de contraseña segura, compartidas por todo el sitio: registro,
recuperación de contraseña, usuarios creados desde el panel y el comando
crear_admin. En el navegador, core/static/js/contrasena.js muestra las
mismas reglas mientras se escribe (si se cambia una regla aquí, hay que
cambiarla también allá).
"""

LARGO_MINIMO_CONTRASENA = 8

REGLAS_CONTRASENA = (
    f'mínimo {LARGO_MINIMO_CONTRASENA} caracteres, al menos un número y al menos una letra mayúscula'
)


def errores_contrasena(contrasena):
    """Lista de lo que le falta a la contraseña (vacía si cumple todo)."""
    errores = []
    if len(contrasena) < LARGO_MINIMO_CONTRASENA:
        errores.append(f'La contraseña debe tener al menos {LARGO_MINIMO_CONTRASENA} caracteres.')
    if not any(c.isdigit() for c in contrasena):
        errores.append('La contraseña debe tener al menos un número.')
    if not any(c.isupper() for c in contrasena):
        errores.append('La contraseña debe tener al menos una letra mayúscula.')
    return errores
