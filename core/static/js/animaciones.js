// ═══════════════════════════════════════════════════════════════════════
// Animaciones del sitio público (estilos en core/static/css/animaciones.css)
//
// 1. Aparición progresiva al hacer scroll: cada bloque de la lista
//    REVELAR recibe [data-anim] y, cuando entra en pantalla, la clase
//    .anim-visible. Los que entran juntos aparecen en cascada.
// 2. Transición entre módulos: al hacer clic en un enlace interno, el
//    telón con el logo cubre la página y luego se navega; la página
//    nueva arranca con el telón puesto y lo retira (ver el <head> de
//    base.html, que lee la marca de sessionStorage).
// 3. Barra de progreso de lectura arriba de la página.
//
// Solo corre si el <head> de base.html puso .anim-on en <html> (no lo
// pone cuando el sistema pide reducir el movimiento).
// ═══════════════════════════════════════════════════════════════════════

(function () {
    const html = document.documentElement;
    if (!html.classList.contains("anim-on")) return;

    // Bloques que se animan: [selector, tipo de animación].
    // Tipos: subir, aparecer, izquierda, derecha, zoom, titulo, linea
    // (definidos en animaciones.css). No se incluyen los elementos que ya
    // tienen su propia animación: el hero de inicio (inicio.js), las fotos
    // de la galería (galeria.js) y las tarjetas de testimonios
    // (testimonios.js).
    const REVELAR = [
        // Información
        [".info-eyebrow", "subir"],
        [".info-hero-content h1", "titulo"],
        [".info-hero-content p", "subir"],
        [".info-hero-line", "linea"],
        [".info-hero-number", "aparecer"],
        [".info-about-visual", "izquierda"],
        [".info-about-content > .info-kicker", "subir"],
        [".info-about-content > h2", "titulo"],
        [".info-about-content > p", "subir"],
        [".info-value", "derecha"],
        [".info-vision-heading .info-kicker", "subir"],
        [".info-vision-title", "titulo"],
        [".info-vision-content > *", "derecha"],
        [".info-gold-line", "linea"],
        [".info-mision-content > *", "subir"],
        [".info-final-button", "zoom"],

        // Testimonios (las tarjetas las anima testimonios.js)
        [".testimonios-header h2", "titulo"],
        [".testimonios-header .hero-separador", "aparecer"],
        [".testimonios-paginacion", "subir"],
        [".testimonios-decorador-seccion", "aparecer"],
        [".formulario-testimonio", "subir"],
        [".login-testimonio", "subir"],

        // Galería (las fotos las anima galeria.js)
        [".ga-hero-tag", "subir"],
        [".ga-hero h1", "titulo"],
        [".ga-hero-linea", "linea"],
        [".ga-hero p", "subir"],
        [".ga-selector-titulo", "subir"],
        [".ga-grupo", "subir"],
        [".ga-barra .container > *", "aparecer"],
        [".ga-cta .container > *", "subir"],

        // Catálogo de alquiler
        [".catalogo-header h1", "titulo"],
        [".catalogo-header p", "subir"],
        [".filtro-categorias", "subir"],
        [".item-card", "zoom"],
        [".panel-cotizacion", "aparecer"],

        // Salones (convenios)
        [".salones-header h1", "titulo"],
        [".salones-header p", "subir"],
        [".aviso-login-salones", "subir"],
        [".salon-card", "zoom"],

        // Contacto
        [".contacto-header h2", "titulo"],
        [".contacto-header p", "subir"],
        [".formulario-card", "izquierda"],
        [".info-card", "derecha"],
        [".hablemos-card", "subir"],

        // Footer (todas las páginas)
        [".footer-content > div", "subir"],
        [".copyright", "aparecer"],
    ];

    // Las líneas que están centradas crecen desde el centro.
    const LINEAS_CENTRADAS = ".ga-hero-linea, .info-mision-content .info-gold-line";

    // Nunca se anima nada dentro de modales, la burbuja de contacto ni el
    // visor de fotos: se muestran/ocultan solos y no dependen del scroll.
    const EXCLUIR = ".modal, .login-modal-overlay, .jm-widget, .ga-visor";

    const PASO_CASCADA = 0.09;   // segundos entre un bloque y el siguiente
    const MAX_CASCADA = 0.6;     // tope para que nada espere demasiado
    const DURACION_SALIDA = 450; // ms del telón antes de navegar

    // ── 1. Aparición progresiva al hacer scroll ───────────────────────

    const marcados = [];
    REVELAR.forEach(([selector, tipo]) => {
        document.querySelectorAll(selector).forEach((el) => {
            if (el.hasAttribute("data-anim") || el.closest(EXCLUIR)) return;
            el.setAttribute("data-anim", tipo);
            if (tipo === "linea" && el.matches(LINEAS_CENTRADAS)) {
                el.setAttribute("data-anim-centro", "");
            }
            marcados.push(el);
        });
    });

    function mostrar(el, retraso) {
        el.style.setProperty("--anim-retraso", retraso + "s");
        el.classList.add("anim-visible");
    }

    // Al terminar se quita la animación (ver .anim-terminado en el CSS).
    document.addEventListener("animationend", (event) => {
        const el = event.target;
        if (el.hasAttribute && el.hasAttribute("data-anim") && el.classList.contains("anim-visible")) {
            el.classList.add("anim-terminado");
            el.style.removeProperty("--anim-retraso");
        }
    });

    // Al llegar al final de la página se muestra lo que quede pendiente
    // (lo último del footer nunca alcanza a cruzar el margen inferior).
    let observador = null;
    function mostrarPendientes() {
        let i = 0;
        marcados.forEach((el) => {
            if (el.classList.contains("anim-visible")) return;
            mostrar(el, Math.min(i++ * PASO_CASCADA, MAX_CASCADA));
            if (observador) observador.unobserve(el);
        });
    }

    if (!("IntersectionObserver" in window)) {
        marcados.forEach((el) => el.classList.add("anim-visible", "anim-terminado"));
    } else {
        observador = new IntersectionObserver((entradas) => {
            // Los que entran en el mismo momento aparecen en cascada,
            // en el orden en que están en la página.
            const visibles = entradas
                .filter((entrada) => entrada.isIntersecting)
                .map((entrada) => entrada.target)
                .sort((a, b) =>
                    a.compareDocumentPosition(b) & Node.DOCUMENT_POSITION_FOLLOWING ? -1 : 1
                );

            visibles.forEach((el, i) => {
                mostrar(el, Math.min(i * PASO_CASCADA, MAX_CASCADA));
                observador.unobserve(el);
            });
        }, { rootMargin: "0px 0px -8% 0px", threshold: 0 });

        marcados.forEach((el) => {
            // Lo que ya quedó por encima de la pantalla (por ejemplo, al
            // recargar a mitad de página) se muestra sin animación.
            if (el.getBoundingClientRect().bottom < 0) {
                el.classList.add("anim-visible", "anim-terminado");
            } else {
                observador.observe(el);
            }
        });
    }

    // Catálogo: al cambiar de filtro, las tarjetas que quedan visibles
    // vuelven a entrar en cascada. catalogo.js ya hizo el filtrado cuando
    // este listener (en window) se ejecuta.
    window.addEventListener("click", (event) => {
        if (!event.target.closest || !event.target.closest(".btn-filtro")) return;
        const tarjetas = document.querySelectorAll(".item-card-wrapper .item-card.anim-visible");
        let i = 0;
        tarjetas.forEach((tarjeta) => {
            if (tarjeta.closest(".item-card-wrapper").style.display === "none") return;
            tarjeta.classList.remove("anim-visible", "anim-terminado");
            void tarjeta.offsetWidth; // reinicia la animación
            mostrar(tarjeta, Math.min(i++ * 0.05, MAX_CASCADA));
        });
    });

    // ── 2. Transición entre módulos ───────────────────────────────────

    function esNavegacionInterna(event, enlace) {
        if (event.defaultPrevented || event.button !== 0) return false;
        if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return false;
        if (enlace.target && enlace.target !== "_self") return false;
        if (enlace.hasAttribute("download") || enlace.hasAttribute("data-bs-toggle")) return false;

        const destino = enlace.getAttribute("href");
        if (!destino || destino.startsWith("#") || destino.startsWith("javascript:")) return false;

        const url = new URL(enlace.href, window.location.href);
        if (url.origin !== window.location.origin) return false;
        if (!/^https?:$/.test(url.protocol)) return false;
        // Mismo documento con otro #ancla: lo resuelve el scroll suave.
        if (url.pathname === window.location.pathname &&
            url.search === window.location.search && url.hash) return false;
        // El panel de administrador y el admin de Django no usan base.html.
        if (/^\/(panel-admin|admin)\//.test(url.pathname)) return false;
        return true;
    }

    // En window (y no en document) para correr después de los demás
    // scripts: si alguno canceló el clic (p. ej. abrir la modal de login),
    // event.defaultPrevented ya lo indica y no se hace la transición.
    window.addEventListener("click", (event) => {
        const enlace = event.target.closest && event.target.closest("a[href]");
        if (!enlace || !esNavegacionInterna(event, enlace)) return;

        event.preventDefault();
        try { sessionStorage.setItem("pe-transicion", "1"); } catch (e) { /* sin storage: entra sin telón */ }
        html.classList.add("anim-saliendo");
        setTimeout(() => { window.location.href = enlace.href; }, DURACION_SALIDA);
    });

    // Al volver con el botón "atrás" el navegador puede restaurar la
    // página tal como quedó (con el telón puesto): se retira.
    window.addEventListener("pageshow", (event) => {
        if (event.persisted) {
            html.classList.remove("anim-saliendo");
            try { sessionStorage.removeItem("pe-transicion"); } catch (e) { /* nada */ }
        }
    });

    // ── 3. Barra de progreso de lectura ───────────────────────────────

    const barra = document.createElement("div");
    barra.className = "anim-progreso";
    barra.setAttribute("aria-hidden", "true");
    document.body.appendChild(barra);

    let pendiente = false;
    function actualizarBarra() {
        pendiente = false;
        const total = document.documentElement.scrollHeight - window.innerHeight;
        const avance = total > 0 ? Math.min(window.scrollY / total, 1) : 0;
        barra.style.scale = avance + " 1";
        barra.classList.toggle("is-activa", window.scrollY > 4);
        if (total > 0 && window.scrollY >= total - 2) mostrarPendientes();
    }
    function pedirActualizacion() {
        if (!pendiente) {
            pendiente = true;
            requestAnimationFrame(actualizarBarra);
        }
    }
    window.addEventListener("scroll", pedirActualizacion, { passive: true });
    window.addEventListener("resize", pedirActualizacion);
    actualizarBarra();

    // Todo listo: se muestra el contenido y se retira el telón.
    requestAnimationFrame(() => html.classList.add("anim-listo"));
})();
