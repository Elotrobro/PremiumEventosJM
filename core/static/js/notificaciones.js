// ═══════════════════════════════════════════════════════════════════════
// Notificaciones — tarjetas flotantes arriba a la derecha.
//
// Uso desde cualquier script del sitio o del panel:
//     notificar('Texto', 'success' | 'error' | 'warning' | 'info');
//     notificar('Texto', 'error', { titulo: 'Otro título', duracion: 4000 });
//     notificar.siguientePagina('Texto', 'info');  // se muestra al cargar
//                                                 // la próxima página
//
// También se encarga de:
//   - Mostrar los mensajes de Django: cualquier elemento con el atributo
//     data-notificacion="tipo" (ver core/templates/partials/_notificaciones.html).
//   - Reemplazar las burbujas de validación del navegador ("Completa este
//     campo", etc.) por una notificación con el mismo diseño.
//
// Estilos en core/static/css/notificaciones.css.
// ═══════════════════════════════════════════════════════════════════════
(function () {
    'use strict';

    const DURACION = 3000;          // ms que la tarjeta queda en pantalla
    const MAXIMO_VISIBLES = 4;
    const CLAVE_PENDIENTES = 'notificaciones-pendientes';

    const TIPOS = {
        success: { icono: 'fa-circle-check', titulo: '¡Listo!' },
        error: { icono: 'fa-circle-exclamation', titulo: 'Algo salió mal' },
        warning: { icono: 'fa-triangle-exclamation', titulo: 'Atención' },
        info: { icono: 'fa-circle-info', titulo: 'Información' },
    };
    // Niveles de Django que no tienen diseño propio.
    const ALIAS = { debug: 'info', danger: 'error', exito: 'success', aviso: 'warning' };

    const reducirMovimiento = window.matchMedia &&
        window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    const conPopover = typeof HTMLElement.prototype.showPopover === 'function';

    let pila = null;

    // ── Contenedor ───────────────────────────────────────────────────────
    function obtenerPila() {
        if (pila && pila.isConnected) return pila;
        pila = document.createElement('div');
        pila.className = 'notif-pila';
        pila.setAttribute('aria-live', 'polite');
        if (conPopover) pila.setAttribute('popover', 'manual');
        // Cuando la pila está dentro de una modal, un clic en la tarjeta no
        // debe llegar a la modal (la de cotización se cierra con clics
        // "fuera" de su recuadro, y la tarjeta queda fuera de él).
        ['click', 'mousedown', 'pointerdown'].forEach(function (tipo) {
            pila.addEventListener(tipo, function (e) { e.stopPropagation(); });
        });
        document.body.appendChild(pila);
        return pila;
    }

    // La pila es un popover: así queda en la "capa superior" del navegador,
    // por encima incluso de las modales <dialog> abiertas con showModal().
    // Se vuelve a abrir en cada aviso para quedar encima de la última modal.
    function traerAlFrente() {
        const contenedor = obtenerPila();

        // Una modal <dialog> deja "inerte" todo lo que esté fuera de ella;
        // si hay una abierta, la pila se mueve adentro para que la tarjeta
        // se pueda cerrar o pausar con el mouse.
        const modalAbierta = Array.from(document.querySelectorAll('dialog[open]'))
            .filter(function (d) { return d.matches(':modal'); })
            .pop();
        const destino = modalAbierta || document.body;
        if (contenedor.parentElement !== destino) destino.appendChild(contenedor);

        // Debajo de la barra de navegación (si está a la vista).
        const barra = document.querySelector('nav.navbar, .pa-topbar');
        let tope = 16;
        if (barra) {
            const abajo = barra.getBoundingClientRect().bottom;
            if (abajo > 0) tope = Math.round(abajo + 14);
        }
        contenedor.style.setProperty('--notif-top', tope + 'px');

        if (!conPopover) return;
        try {
            if (contenedor.matches(':popover-open')) contenedor.hidePopover();
            contenedor.showPopover();
        } catch (e) { /* el navegador no permitió abrirlo: queda como fixed */ }
    }

    // Si la modal donde estaba la pila se cierra, las tarjetas que sigan en
    // pantalla vuelven al <body> para no desaparecer con ella.
    document.addEventListener('close', function (evento) {
        if (!pila || evento.target.tagName !== 'DIALOG' || !evento.target.contains(pila)) return;
        if (pila.querySelector('.notif:not(.notif-saliendo)')) {
            traerAlFrente();
        } else {
            document.body.appendChild(pila);
        }
    }, true);

    function cerrarPilaSiVacia() {
        if (!pila || pila.querySelector('.notif:not(.notif-saliendo)')) return;
        if (conPopover && pila.matches(':popover-open')) {
            try { pila.hidePopover(); } catch (e) { /* nada */ }
        }
    }

    // ── Tarjeta ──────────────────────────────────────────────────────────
    function crearTarjeta(texto, tipo, titulo) {
        const tarjeta = document.createElement('div');
        tarjeta.className = 'notif notif-' + tipo;
        tarjeta.setAttribute('role', tipo === 'error' || tipo === 'warning' ? 'alert' : 'status');

        const icono = document.createElement('div');
        icono.className = 'notif-icono';
        icono.innerHTML = '<i class="fas ' + TIPOS[tipo].icono + '" aria-hidden="true"></i>';

        const cuerpo = document.createElement('div');
        cuerpo.className = 'notif-cuerpo';
        const h = document.createElement('p');
        h.className = 'notif-titulo';
        h.textContent = titulo;
        const p = document.createElement('p');
        p.className = 'notif-texto';
        p.textContent = texto;
        cuerpo.append(h, p);

        const cerrar = document.createElement('button');
        cerrar.type = 'button';
        cerrar.className = 'notif-cerrar';
        cerrar.setAttribute('aria-label', 'Cerrar notificación');
        cerrar.innerHTML = '<i class="fas fa-xmark" aria-hidden="true"></i>';

        const progreso = document.createElement('div');
        progreso.className = 'notif-progreso';

        const brillo = document.createElement('span');
        brillo.className = 'notif-brillo';

        tarjeta.append(brillo, icono, cuerpo, cerrar, progreso);
        return tarjeta;
    }

    function animarEntrada(tarjeta) {
        if (reducirMovimiento) {
            tarjeta.animate([{ opacity: 0 }, { opacity: 1 }], { duration: 200, easing: 'ease-out' });
            return;
        }
        // La tarjeta entra desde la derecha, desenfocada y un poco más
        // pequeña, con un leve rebote al llegar.
        tarjeta.animate([
            { opacity: 0, transform: 'translateX(115%) scale(0.86) rotate(2deg)', filter: 'blur(6px)' },
            { opacity: 1, transform: 'translateX(-10px) scale(1.02) rotate(-0.4deg)', filter: 'blur(0)', offset: 0.62 },
            { opacity: 1, transform: 'translateX(3px) scale(0.995)', offset: 0.82 },
            { opacity: 1, transform: 'translateX(0) scale(1)', filter: 'blur(0)' },
        ], { duration: 720, easing: 'cubic-bezier(0.22, 1, 0.36, 1)' });

        // El icono "salta" en cuanto la tarjeta llega.
        tarjeta.querySelector('.notif-icono').animate([
            { transform: 'scale(0) rotate(-120deg)', opacity: 0 },
            { transform: 'scale(1.25) rotate(10deg)', opacity: 1, offset: 0.6 },
            { transform: 'scale(1) rotate(0)', opacity: 1 },
        ], { duration: 560, delay: 260, easing: 'cubic-bezier(0.34, 1.56, 0.64, 1)', fill: 'backwards' });

        // Título y texto aparecen en cascada.
        tarjeta.querySelectorAll('.notif-titulo, .notif-texto').forEach(function (el, i) {
            el.animate([
                { opacity: 0, transform: 'translateY(6px)' },
                { opacity: 1, transform: 'translateY(0)' },
            ], { duration: 420, delay: 320 + i * 90, easing: 'ease-out', fill: 'backwards' });
        });

        // Destello dorado que cruza la tarjeta.
        tarjeta.querySelector('.notif-brillo').animate([
            { transform: 'translateX(-120%)' },
            { transform: 'translateX(120%)' },
        ], { duration: 900, delay: 420, easing: 'ease-in-out' });
    }

    function animarSalida(tarjeta) {
        if (reducirMovimiento) {
            return tarjeta.animate([{ opacity: 1 }, { opacity: 0 }], { duration: 200, fill: 'forwards' }).finished;
        }
        const alto = tarjeta.offsetHeight;
        // Se desliza hacia la derecha encogiéndose, y luego cierra su hueco
        // para que las demás tarjetas suban suavemente.
        const fuera = tarjeta.animate([
            { opacity: 1, transform: 'translateX(0) scale(1)', filter: 'blur(0)' },
            { opacity: 1, transform: 'translateX(-14px) scale(1.01)', offset: 0.25 },
            { opacity: 0, transform: 'translateX(110%) scale(0.88)', filter: 'blur(4px)' },
        ], { duration: 520, easing: 'cubic-bezier(0.55, 0, 0.75, 0.2)', fill: 'forwards' });

        return fuera.finished.then(function () {
            return tarjeta.animate([
                { height: alto + 'px', marginBottom: '12px', paddingTop: '14px', paddingBottom: '16px' },
                { height: '0px', marginBottom: '0px', paddingTop: '0px', paddingBottom: '0px' },
            ], { duration: 260, easing: 'ease-in-out', fill: 'forwards' }).finished;
        });
    }

    function cerrarTarjeta(tarjeta) {
        if (tarjeta.classList.contains('notif-saliendo')) return;
        tarjeta.classList.add('notif-saliendo');
        if (tarjeta._progreso) tarjeta._progreso.cancel();
        animarSalida(tarjeta).catch(function () { /* animación cancelada */ }).then(function () {
            tarjeta.remove();
            cerrarPilaSiVacia();
        });
    }

    // El tiempo en pantalla lo marca la barra de progreso: al terminar de
    // vaciarse se cierra la tarjeta. Con el mouse encima se pausa.
    function iniciarTemporizador(tarjeta, duracion) {
        if (tarjeta._progreso) tarjeta._progreso.cancel();
        const animacion = tarjeta.querySelector('.notif-progreso').animate(
            [{ transform: 'scaleX(1)' }, { transform: 'scaleX(0)' }],
            { duration: duracion, easing: 'linear', fill: 'forwards' }
        );
        tarjeta._progreso = animacion;
        animacion.finished.then(function () { cerrarTarjeta(tarjeta); }).catch(function () { /* reiniciada */ });
    }

    // Los mensajes largos (ej. el código de seguimiento de una cotización)
    // necesitan algo más de tiempo para leerse; los normales duran 3 s.
    function duracionPara(texto) {
        const extra = Math.max(0, texto.length - 90) * 35;
        return Math.min(DURACION + extra, 9000);
    }

    function notificar(texto, tipo, opciones) {
        texto = String(texto == null ? '' : texto).trim();
        if (!texto) return null;
        tipo = ALIAS[tipo] || tipo;
        if (!TIPOS[tipo]) tipo = 'info';
        opciones = opciones || {};
        const titulo = opciones.titulo || TIPOS[tipo].titulo;
        const duracion = opciones.duracion || duracionPara(texto);

        traerAlFrente();
        const contenedor = obtenerPila();

        // Si el mismo aviso ya está en pantalla, se reinicia en vez de repetirlo.
        const repetida = Array.from(contenedor.querySelectorAll('.notif:not(.notif-saliendo)')).find(function (t) {
            return t.dataset.clave === tipo + '|' + titulo + '|' + texto;
        });
        if (repetida) {
            repetida.animate([
                { transform: 'translateX(0)' }, { transform: 'translateX(-8px)' },
                { transform: 'translateX(6px)' }, { transform: 'translateX(0)' },
            ], { duration: 360, easing: 'ease-in-out' });
            iniciarTemporizador(repetida, duracion);
            return repetida;
        }

        const tarjeta = crearTarjeta(texto, tipo, titulo);
        tarjeta.dataset.clave = tipo + '|' + titulo + '|' + texto;
        contenedor.appendChild(tarjeta);

        const activas = contenedor.querySelectorAll('.notif:not(.notif-saliendo)');
        for (let i = 0; i < activas.length - MAXIMO_VISIBLES; i++) cerrarTarjeta(activas[i]);

        animarEntrada(tarjeta);
        iniciarTemporizador(tarjeta, duracion);

        tarjeta.querySelector('.notif-cerrar').addEventListener('click', function () { cerrarTarjeta(tarjeta); });
        tarjeta.addEventListener('mouseenter', function () { if (tarjeta._progreso) tarjeta._progreso.pause(); });
        tarjeta.addEventListener('mouseleave', function () {
            if (tarjeta._progreso && !tarjeta.classList.contains('notif-saliendo')) tarjeta._progreso.play();
        });
        return tarjeta;
    }

    notificar.exito = function (texto, op) { return notificar(texto, 'success', op); };
    notificar.error = function (texto, op) { return notificar(texto, 'error', op); };
    notificar.aviso = function (texto, op) { return notificar(texto, 'warning', op); };
    notificar.info = function (texto, op) { return notificar(texto, 'info', op); };

    // Para avisos que deben verse después de enviar un formulario (la página
    // se recarga y una notificación normal desaparecería con ella).
    notificar.siguientePagina = function (texto, tipo, opciones) {
        try {
            const lista = JSON.parse(sessionStorage.getItem(CLAVE_PENDIENTES) || '[]');
            lista.push({ texto: texto, tipo: tipo, opciones: opciones || {} });
            sessionStorage.setItem(CLAVE_PENDIENTES, JSON.stringify(lista));
        } catch (e) { /* sin sessionStorage: no se guarda */ }
    };

    window.notificar = notificar;

    // ── Validación de formularios ────────────────────────────────────────
    // El navegador dispara "invalid" en cada campo que no cumple sus reglas
    // (required, type="email", minlength, pattern, setCustomValidity…).
    // Se cancela la burbuja nativa y se muestra la notificación del sitio
    // con el primer error, marcando el campo en rojo.

    function nombreCampo(campo) {
        let texto = '';
        if (campo.type === 'radio') {
            const grupo = campo.closest('fieldset');
            const leyenda = grupo && grupo.querySelector('legend');
            if (leyenda) texto = leyenda.textContent;
        }
        if (!texto && campo.labels && campo.labels.length) {
            texto = Array.from(campo.labels[0].childNodes)
                .filter(function (n) { return n.nodeType === Node.TEXT_NODE || !n.matches('input, select, textarea'); })
                .map(function (n) { return n.textContent; }).join(' ');
        }
        // Campos sin <label for> (ej. la calificación con estrellas de
        // testimonios): se usa la etiqueta del bloque que los contiene.
        if (!texto) {
            const bloque = campo.closest('.form-group, .campo-testimonio, .mb-3, fieldset');
            const etiqueta = bloque && bloque.querySelector('label:not([for]), legend');
            if (etiqueta) texto = etiqueta.textContent;
        }
        texto = texto || campo.getAttribute('aria-label') || campo.getAttribute('placeholder') || '';
        texto = texto.replace(/\s+/g, ' ').replace(/[*:]\s*$/, '').trim();
        return texto.length > 60 ? '' : texto;
    }

    function formatearFecha(valor) {
        const partes = /^(\d{4})-(\d{2})-(\d{2})$/.exec(valor || '');
        return partes ? partes[3] + '/' + partes[2] + '/' + partes[1] : valor;
    }

    function mensajeValidacion(campo) {
        const v = campo.validity;
        const nombre = nombreCampo(campo);
        const el = nombre ? ' «' + nombre + '»' : '';
        const tipo = (campo.type || '').toLowerCase();

        if (v.customError) return campo.validationMessage;
        if (v.valueMissing) {
            if (tipo === 'checkbox') return nombre ? 'Marca la casilla' + el + ' para continuar.' : 'Marca esta casilla para continuar.';
            if (tipo === 'radio' || campo.tagName === 'SELECT') return 'Selecciona una opción' + (nombre ? ' en' + el : '') + '.';
            if (tipo === 'file') return 'Selecciona un archivo' + (nombre ? ' en' + el : '') + '.';
            return nombre ? 'El campo' + el + ' es obligatorio.' : 'Completa este campo.';
        }
        if (v.typeMismatch) {
            if (tipo === 'email') return 'Ingresa un correo electrónico válido. Ejemplo: usuario@gmail.com';
            if (tipo === 'url') return 'Ingresa una dirección web válida (por ejemplo, https://…).';
            return 'El valor de' + (el || ' este campo') + ' no tiene un formato válido.';
        }
        if (v.badInput) {
            if (tipo === 'number') return 'Ingresa solo números' + (nombre ? ' en' + el : '') + '.';
            return 'Ingresa un valor válido' + (nombre ? ' en' + el : '') + '.';
        }
        if (v.patternMismatch) {
            if (campo.title) return (nombre ? nombre + ': ' : '') + campo.title;
            return 'El formato de' + (el || ' este campo') + ' no es válido.';
        }
        if (v.tooShort) {
            return (nombre ? 'El campo' + el : 'Este campo') + ' debe tener al menos ' + campo.minLength +
                ' caracteres (llevas ' + campo.value.length + ').';
        }
        if (v.tooLong) return (nombre ? 'El campo' + el : 'Este campo') + ' admite máximo ' + campo.maxLength + ' caracteres.';
        if (v.rangeUnderflow) {
            if (tipo === 'date') return 'La fecha' + (nombre ? ' de' + el : '') + ' no puede ser anterior al ' + formatearFecha(campo.min) + '.';
            return (nombre ? 'El campo' + el : 'El valor') + ' debe ser como mínimo ' + campo.min + '.';
        }
        if (v.rangeOverflow) {
            if (tipo === 'date') return 'La fecha' + (nombre ? ' de' + el : '') + ' no puede ser posterior al ' + formatearFecha(campo.max) + '.';
            return (nombre ? 'El campo' + el : 'El valor') + ' debe ser como máximo ' + campo.max + '.';
        }
        if (v.stepMismatch) return 'Ingresa un valor válido' + (nombre ? ' en' + el : '') + '.';
        return campo.validationMessage || 'Revisa este campo.';
    }

    function enfocarCampo(campo) {
        const visible = campo.offsetParent !== null || campo.getClientRects().length > 0;
        const objetivo = visible ? campo : (campo.closest('.form-group, .campo-testimonio, fieldset, label, div') || campo);
        try { objetivo.scrollIntoView({ behavior: reducirMovimiento ? 'auto' : 'smooth', block: 'center' }); } catch (e) { /* nada */ }
        if (visible) {
            try { campo.focus({ preventScroll: true }); } catch (e) { campo.focus(); }
        }
    }

    let avisoEnCurso = false;
    document.addEventListener('invalid', function (evento) {
        const campo = evento.target;
        if (!campo || !campo.validity) return;
        evento.preventDefault();                         // sin burbuja del navegador
        campo.classList.add('notif-campo-invalido');
        campo.setAttribute('aria-invalid', 'true');

        // Al enviar, el navegador avisa de todos los campos inválidos a la
        // vez; solo se muestra el primero (el mismo que mostraba Chrome).
        if (avisoEnCurso) return;
        avisoEnCurso = true;
        setTimeout(function () { avisoEnCurso = false; }, 0);

        notificar(mensajeValidacion(campo), 'error', { titulo: 'Revisa el formulario' });
        enfocarCampo(campo);
    }, true);

    // Quita la marca roja en cuanto el campo queda bien.
    function revisarMarca(evento) {
        const campo = evento.target;
        if (!campo || !campo.classList || !campo.classList.contains('notif-campo-invalido')) return;
        if (campo.validity && campo.validity.valid) {
            campo.classList.remove('notif-campo-invalido');
            campo.removeAttribute('aria-invalid');
        }
    }
    document.addEventListener('input', revisarMarca, true);
    document.addEventListener('change', revisarMarca, true);

    // ── Avisos que vienen en el HTML (mensajes de Django) ───────────────
    function mostrarAvisosDeLaPagina() {
        const avisos = [];

        try {
            const pendientes = JSON.parse(sessionStorage.getItem(CLAVE_PENDIENTES) || '[]');
            sessionStorage.removeItem(CLAVE_PENDIENTES);
            pendientes.forEach(function (a) { avisos.push(a); });
        } catch (e) { /* nada */ }

        document.querySelectorAll('[data-notificacion]').forEach(function (el) {
            avisos.push({ texto: el.textContent, tipo: el.dataset.notificacion, opciones: {} });
            el.remove();
        });

        // Un pequeño retraso para que se vea la animación con la página ya pintada.
        avisos.forEach(function (a, i) {
            setTimeout(function () { notificar(a.texto, a.tipo, a.opciones); }, 350 + i * 180);
        });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', mostrarAvisosDeLaPagina);
    } else {
        mostrarAvisosDeLaPagina();
    }
})();
