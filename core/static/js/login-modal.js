// Controla la ventana modal de cuenta (vive en base.html, así que estas
// funciones aplican en cualquier página del sitio). La misma modal tiene
// dos pestañas: iniciar sesión y crear cuenta.
document.addEventListener('DOMContentLoaded', () => {
    const overlay = document.getElementById('loginModalOverlay');
    const closeBtn = document.getElementById('loginModalClose');
    const navLoginBtn = document.getElementById('navLoginBtn');
    const form = document.getElementById('loginForm');

    if (!overlay) return;

    // ── Pestañas ────────────────────────────────────────────────────
    // Cada pestaña muestra su panel y cambia el título de la modal.
    const TITULOS = {
        login: { titulo: 'Iniciar Sesión', subtitulo: 'Accede a tu cuenta' },
        registro: { titulo: 'Crear Cuenta', subtitulo: 'Regístrate para cotizar tu evento' },
    };
    const pestanas = document.querySelectorAll('.auth-tab');
    const paneles = {
        login: document.getElementById('authPanelLogin'),
        registro: document.getElementById('authPanelRegistro'),
    };
    const titulo = document.getElementById('authTitulo');
    const subtitulo = document.getElementById('authSubtitulo');

    function mostrarPestana(nombre) {
        pestanas.forEach(pestana => {
            const activa = pestana.dataset.tab === nombre;
            pestana.classList.toggle('is-active', activa);
            pestana.setAttribute('aria-selected', activa ? 'true' : 'false');
        });
        Object.entries(paneles).forEach(([clave, panel]) => {
            if (panel) panel.classList.toggle('is-active', clave === nombre);
        });
        titulo.textContent = TITULOS[nombre].titulo;
        subtitulo.textContent = TITULOS[nombre].subtitulo;
    }

    pestanas.forEach(pestana => {
        pestana.addEventListener('click', () => mostrarPestana(pestana.dataset.tab));
    });

    // Enlaces "¿No tienes cuenta? Regístrate" / "¿Ya tienes cuenta?"
    document.querySelectorAll('[data-ir-a]').forEach(enlace => {
        enlace.addEventListener('click', () => mostrarPestana(enlace.dataset.irA));
    });

    // El backend decide con qué pestaña se abre: registro_view redirige
    // con ?registro=1 cuando el registro falló, para que los errores se
    // vean en la pestaña correcta (ver data-open-tab en base.html).
    mostrarPestana(document.body.dataset.openTab === 'registro' ? 'registro' : 'login');

    function abrirLoginModal() {
        overlay.classList.add('is-open');
        document.body.style.overflow = 'hidden'; // evita el scroll de fondo mientras está abierta
    }

    // Se expone en window para que otros scripts del sitio (modal.js de la
    // cotización, catalogo.js del carrito) puedan abrir esta misma modal
    // sin necesidad de navegar a otra URL cuando detectan que hace falta
    // iniciar sesión.
    window.abrirLoginModal = abrirLoginModal;

    function cerrarLoginModal() {
        overlay.classList.remove('is-open');
        document.body.style.overflow = '';
    }

    // Abrir desde el link "Iniciar Sesión" del menú
    if (navLoginBtn) {
        navLoginBtn.addEventListener('click', (event) => {
            event.preventDefault();
            abrirLoginModal();
        });
    }

    // Cerrar con la "X"
    if (closeBtn) {
        closeBtn.addEventListener('click', cerrarLoginModal);
    }

    // Cerrar haciendo clic fuera de la tarjeta (en el fondo oscuro)
    overlay.addEventListener('click', (event) => {
        if (event.target === overlay) {
            cerrarLoginModal();
        }
    });

    // Cerrar con la tecla Escape
    document.addEventListener('keydown', (event) => {
        if (event.key === 'Escape' && overlay.classList.contains('is-open')) {
            cerrarLoginModal();
        }
    });

    // Auto-abrir si el backend pide que se muestre de nuevo: esto pasa
    // cuando las credenciales fueron incorrectas, o cuando algún flujo del
    // sitio (cotizar sin sesión, etc.) redirige aquí con ?login=1
    // (ver Bd_PremiumEventos/views.py -> login_view).
    if (document.body.dataset.openLogin === 'true') {
        abrirLoginModal();
    }

    // Validación básica en el cliente. El inicio de sesión real (contra la
    // base de datos) lo hace el backend en Bd_PremiumEventos/views.py; esto
    // solo evita envíos con campos vacíos o correos con formato inválido
    // antes de llegar al servidor.
    if (form) {
        form.addEventListener('submit', (event) => {
            const email = document.getElementById('loginEmail').value.trim();
            const password = document.getElementById('loginPassword').value;

            if (!email || !password) {
                event.preventDefault();
                alert('Por favor completa todos los campos');
                return;
            }

            if (!email.includes('@')) {
                event.preventDefault();
                alert('Ingresa un correo electrónico válido');
                return;
            }

            // Los campos son válidos: se deja continuar el envío normal del
            // formulario (POST a /login/), donde Django valida las credenciales.
        });
    }

    // Registro: el formulario no lleva novalidate, así que el navegador ya
    // exige los campos obligatorios, el formato del correo y el mínimo de
    // 8 caracteres. Aquí solo se agrega lo que el HTML no puede comprobar:
    // que las dos contraseñas coincidan. El correo repetido lo valida el
    // servidor (ver registro_view), que es quien consulta la base de datos.
    const formRegistro = document.getElementById('registroForm');
    if (formRegistro) {
        const password = document.getElementById('registroPassword');
        const confirmacion = document.getElementById('registroPassword2');

        const revisarCoincidencia = () => {
            confirmacion.setCustomValidity(
                confirmacion.value && password.value !== confirmacion.value
                    ? 'Las contraseñas no coinciden.'
                    : ''
            );
        };

        password.addEventListener('input', revisarCoincidencia);
        confirmacion.addEventListener('input', revisarCoincidencia);
    }
});
