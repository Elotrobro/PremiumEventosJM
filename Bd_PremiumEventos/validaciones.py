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


# ─────────────────────────────────────────────────────────────────────────
# Nombres y apellidos (registro, contacto, cotización y panel)
# ─────────────────────────────────────────────────────────────────────────
# Además de letras (con tildes y ñ) se permiten espacios y los signos que
# aparecen en nombres reales: María-José, O'Neil, Ma. Fernanda.
SIGNOS_PERMITIDOS_NOMBRE = " '-."

# En las plantillas, los <input> de nombre llevan el mismo filtro en
# pattern="[A-Za-zÀ-ÖØ-öø-ÿ' .\-]+" para que el navegador avise antes de
# enviar; el servidor siempre vuelve a revisar con errores_nombre.


def limpiar_nombre(valor):
    """Quita espacios sobrantes: '  ana   maría ' → 'ana maría'."""
    return ' '.join(valor.split())


def errores_nombre(valor, campo='el nombre'):
    """
    Lista de errores del nombre (vacía si es válido). Recibe el valor ya
    limpio; `campo` va en minúscula y con artículo ("el nombre", "los apellidos").
    """
    if not valor:
        return [f'Completa {campo}.']
    if not all(c.isalpha() or c in SIGNOS_PERMITIDOS_NOMBRE for c in valor):
        return [f'En {campo} solo se permiten letras y espacios (sin números, @ ni otros símbolos).']
    if sum(c.isalpha() for c in valor) < 2:
        return [f'Escribe al menos 2 letras en {campo}.']
    return []
