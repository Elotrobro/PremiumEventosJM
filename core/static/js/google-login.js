// ═══════════════════════════════════════════════════════════════════════
// "Continuar con Google" en la modal de cuenta (base.html).
//
// - El script oficial de Google (accounts.google.com/gsi/client) se carga
//   solo la primera vez que se abre la modal, no en cada página.
// - Pinta el botón oficial en las pestañas "Iniciar sesión" y "Crear
//   cuenta" (los <div data-google-boton>).
// - En "Crear cuenta" el botón queda bloqueado hasta marcar las casillas de
//   Términos y Política de privacidad, y su valor viaja con el formulario
//   (google_login.py no crea cuentas nuevas sin esa autorización).
// - Cuando la persona elige su cuenta, Google entrega un token firmado; se
//   envía con el formulario oculto #googleLoginForm a /login/google/, donde
//   Django lo verifica (Bd_PremiumEventos/google_login.py).
//
// Si GOOGLE_CLIENT_ID no está en el .env, base.html no pone ni el botón ni
// el formulario y este script no hace nada.
// ═══════════════════════════════════════════════════════════════════════
(function () {
    'use strict';

    const form = document.getElementById('googleLoginForm');
    const overlay = document.getElementById('loginModalOverlay');
    const contenedores = Array.from(document.querySelectorAll('[data-google-boton]'));
    if (!form || !overlay || !contenedores.length) return;

    const clientId = form.dataset.clientId;
    const SCRIPT_GOOGLE = 'https://accounts.google.com/gsi/client';
    let estado = 'sin-cargar';   // 'cargando' | 'listo' | 'error'

    function avisar(texto) {
        if (window.notificar) {
            window.notificar(texto, 'error', { titulo: 'Inicio con Google' });
        }
    }

    function mostrarFallo(texto) {
        contenedores.forEach(function (c) {
            const aviso = document.createElement('span');
            aviso.className = 'google-login-cargando google-login-error';
            aviso.textContent = texto;
            c.replaceChildren(aviso);
        });
    }

    // Pestaña visible en este momento ("login" o "registro"): así, si algo
    // falla, Django vuelve a abrir la modal en la misma pestaña.
    function pestanaActiva() {
        const registro = document.getElementById('authPanelRegistro');
        return registro && registro.classList.contains('is-active') ? 'registro' : 'login';
    }

    // ── Términos y privacidad (casillas de "Crear cuenta") ──────────────
    const casillas = ['registroTerminos', 'registroPrivacidad']
        .map(function (id) { return document.getElementById(id); })
        .filter(Boolean);
    const googleRegistro = document.getElementById('googleRegistro');

    function aceptoTodo() {
        return casillas.length > 0 && casillas.every(function (c) { return c.checked; });
    }

    function actualizarBloqueo() {
        if (!googleRegistro) return;
        const bloqueado = !aceptoTodo();
        googleRegistro.classList.toggle('is-bloqueado', bloqueado);
        googleRegistro.setAttribute('aria-disabled', bloqueado ? 'true' : 'false');
    }

    casillas.forEach(function (c) { c.addEventListener('change', actualizarBloqueo); });
    actualizarBloqueo();

    // Clic en el botón bloqueado: se avisa y se marca la primera casilla pendiente.
    if (googleRegistro) {
        googleRegistro.addEventListener('click', function () {
            if (aceptoTodo()) return;
            const pendiente = casillas.find(function (c) { return !c.checked; });
            if (pendiente) pendiente.reportValidity();   // notificaciones.js muestra el aviso
        });
    }

    function recibirCredencial(respuesta) {
        if (!respuesta || !respuesta.credential) {
            avisar('Google no devolvió tu cuenta. Intenta de nuevo.');
            return;
        }
        form.elements.credential.value = respuesta.credential;
        form.elements.origen.value = pestanaActiva();
        // Las casillas viajan siempre: así una cuenta nueva solo se crea con
        // la autorización, aunque se haya usado el botón de "Iniciar sesión".
        const acepto = aceptoTodo() ? 'on' : '';
        form.elements.acepta_terminos.value = acepto;
        form.elements.acepta_privacidad.value = acepto;
        contenedores.forEach(function (c) { c.classList.add('google-login-enviando'); });
        form.submit();
    }

    // Ancho del botón: el de la columna del formulario (Google acepta 200-400 px).
    // offsetWidth no se ve afectado por la animación de escala de la modal.
    function anchoBoton(contenedor) {
        const panel = contenedor.closest('.auth-panel');
        const referencia = (contenedor.offsetWidth || (panel && panel.offsetWidth) ||
            (document.querySelector('.auth-panel.is-active') || {}).offsetWidth || 320);
        return Math.max(200, Math.min(400, Math.round(referencia)));
    }

    let inicializado = false;

    function pintarBotones() {
        if (!inicializado) {     // Google pide llamar initialize() una sola vez
            google.accounts.id.initialize({
                client_id: clientId,
                callback: recibirCredencial,
                ux_mode: 'popup',
                auto_select: false,
                cancel_on_tap_outside: true,
            });
            inicializado = true;
        }
        contenedores.forEach(function (c) {
            c.replaceChildren();
            google.accounts.id.renderButton(c, {
                type: 'standard',
                theme: 'outline',
                size: 'large',
                shape: 'pill',
                text: c.dataset.texto || 'continue_with',
                logo_alignment: 'center',
                locale: 'es',
                width: anchoBoton(c),
            });
        });
    }

    function cargarGoogle() {
        if (estado !== 'sin-cargar') return;
        estado = 'cargando';
        const script = document.createElement('script');
        script.src = SCRIPT_GOOGLE;
        script.async = true;
        script.onload = function () {
            try {
                pintarBotones();
                estado = 'listo';
            } catch (e) {
                estado = 'error';
                console.error('No se pudo iniciar el botón de Google:', e);
                mostrarFallo('El acceso con Google no está disponible en este momento.');
            }
        };
        script.onerror = function () {
            estado = 'error';
            mostrarFallo('No se pudo cargar el acceso con Google. Revisa tu conexión o desactiva el bloqueador de anuncios.');
        };
        document.head.appendChild(script);
    }

    // Se carga al abrir la modal (login-modal.js le pone la clase is-open).
    if (overlay.classList.contains('is-open')) cargarGoogle();
    new MutationObserver(function () {
        if (overlay.classList.contains('is-open')) cargarGoogle();
    }).observe(overlay, { attributes: true, attributeFilter: ['class'] });

    // La pestaña de registro está oculta al pintar el botón y queda con el
    // ancho por defecto; al mostrarla se vuelve a pintar a su ancho real.
    document.querySelectorAll('.auth-tab, [data-ir-a]').forEach(function (boton) {
        boton.addEventListener('click', function () {
            if (estado === 'listo') {
                setTimeout(pintarBotones, 0);
            }
        });
    });
})();
