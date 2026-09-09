// Controla la ventana modal de inicio de sesión (vive en base.html, así
// que estas funciones aplican en cualquier página del sitio).
document.addEventListener('DOMContentLoaded', () => {
    const overlay = document.getElementById('loginModalOverlay');
    const closeBtn = document.getElementById('loginModalClose');
    const navLoginBtn = document.getElementById('navLoginBtn');
    const form = document.getElementById('loginForm');

    if (!overlay) return;

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
});
