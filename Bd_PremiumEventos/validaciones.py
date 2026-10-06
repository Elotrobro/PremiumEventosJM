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


# ─────────────────────────────────────────────────────────────────────────
# Teléfono / WhatsApp (contacto y cotización)
# ─────────────────────────────────────────────────────────────────────────
# Se aceptan los separadores con que la gente suele escribir un número
# ("+57 300 123-4567", "(604) 444 5555"), pero se guardan solo los dígitos.
# Entre 7 (fijo local) y 15 dígitos (máximo internacional, y el tamaño de
# los campos de teléfono en la base de datos). En las plantillas, el
# <input type="tel"> lleva pattern="[0-9 +\(\)\-]{7,20}" para avisar antes de enviar.
SEPARADORES_TELEFONO = ' +-()'
MIN_DIGITOS_TELEFONO, MAX_DIGITOS_TELEFONO = 7, 15


def limpiar_telefono(valor):
    """'+57 300 123-4567' → '573001234567' (solo dígitos)."""
    return ''.join(c for c in valor if c.isdigit())


def errores_telefono(valor):
    """Lista de errores del teléfono tal como lo escribió la persona (vacía si es válido)."""
    valor = valor.strip()
    if not valor:
        return ['Escribe un número de teléfono.']
    if not all(c.isdigit() or c in SEPARADORES_TELEFONO for c in valor):
        return ['El teléfono solo puede tener números (y si quieres, espacios, guiones, paréntesis o +).']
    digitos = len(limpiar_telefono(valor))
    if not MIN_DIGITOS_TELEFONO <= digitos <= MAX_DIGITOS_TELEFONO:
        return [f'El teléfono debe tener entre {MIN_DIGITOS_TELEFONO} y {MAX_DIGITOS_TELEFONO} dígitos.']
    return []
