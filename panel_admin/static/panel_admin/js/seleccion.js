// ═══════════════════════════════════════════════════════════════════════
// Selección múltiple de los listados del panel.
//
// Trabaja con la barra de _seleccion_masiva.html (#paFormSeleccion) y con
// las casillas de cada registro (input.pa-check name="ids"
// form="paFormSeleccion"). Marca/desmarca, cuenta los seleccionados,
// activa los botones y envía la acción. "Eliminar" pide confirmación en
// la misma ventana modal del panel (#paModal de base_admin.html).
// Shift + clic marca un rango de casillas.
// ═══════════════════════════════════════════════════════════════════════
(function () {
    'use strict';

    const form = document.getElementById('paFormSeleccion');
    if (!form) return;

    const singular = form.dataset.singular || 'registro';
    const plural = form.dataset.plural || 'registros';
    const terminacion = form.dataset.genero === 'f' ? 'a' : 'o';
    const contador = form.querySelector('.pa-seleccion-contador');
    const botones = form.querySelectorAll('[data-accion]');
    const limpiar = form.querySelector('[data-limpiar-seleccion]');
    const textoInicial = contador.textContent;

    function casillas() {
        return Array.from(document.querySelectorAll('input.pa-check[name="ids"][form="paFormSeleccion"]'));
    }

    // Sin casillas (ej. un empleado sin registros que pueda tocar) no
    // tiene sentido mostrar la barra ni la casilla del encabezado.
    if (!casillas().length) {
        form.hidden = true;
        document.querySelectorAll('[data-seleccionar-todos]').forEach(function (c) { c.hidden = true; });
        return;
    }

    function contenedorDe(casilla) {
        return casilla.closest('tr, .pa-cotizacion-card, .pa-galeria-item');
    }

    function marcadas() {
        return casillas().filter(function (c) { return c.checked; });
    }

    function actualizar() {
        const todas = casillas();
        const n = marcadas().length;

        contador.textContent = n
            ? n + ' ' + (n === 1 ? singular + ' seleccionad' + terminacion : plural + ' seleccionad' + terminacion + 's')
            : textoInicial;

        document.querySelectorAll('[data-seleccionar-todos]').forEach(function (c) {
            c.checked = n > 0 && n === todas.length;
            c.indeterminate = n > 0 && n < todas.length;
        });
        botones.forEach(function (b) { b.disabled = n === 0; });
        limpiar.disabled = n === 0;
        form.classList.toggle('pa-seleccion-activa', n > 0);

        todas.forEach(function (c) {
            const fila = contenedorDe(c);
            if (fila) fila.classList.toggle('pa-seleccionado', c.checked);
        });
    }

    // Shift + clic: marca o desmarca todo el rango desde la última casilla.
    let ultima = null;
    document.addEventListener('click', function (e) {
        const casilla = e.target.closest && e.target.closest('input.pa-check[name="ids"]');
        if (!casilla) return;
        const todas = casillas();
        if (e.shiftKey && ultima && ultima !== casilla) {
            const a = todas.indexOf(ultima);
            const b = todas.indexOf(casilla);
            if (a > -1 && b > -1) {
                todas.slice(Math.min(a, b), Math.max(a, b) + 1).forEach(function (c) { c.checked = casilla.checked; });
                actualizar();
            }
        }
        ultima = casilla;
    });

    document.addEventListener('change', function (e) {
        if (!e.target.matches) return;
        if (e.target.matches('[data-seleccionar-todos]')) {
            const valor = e.target.checked;
            casillas().forEach(function (c) { c.checked = valor; });
            actualizar();
        } else if (e.target.matches('input.pa-check[name="ids"]')) {
            actualizar();
        }
    });

    limpiar.addEventListener('click', function () {
        casillas().forEach(function (c) { c.checked = false; });
        actualizar();
    });

    function enviar(accion) {
        form.elements.accion.value = accion;
        botones.forEach(function (b) { b.disabled = true; });
        form.submit();
    }

    // ── Confirmación antes de eliminar ───────────────────────────────────
    function confirmar(boton) {
        const elegidas = marcadas();
        const n = elegidas.length;
        const texto = n + ' ' + (n === 1 ? singular : plural);
        const modalEl = document.getElementById('paModal');

        // Sin la modal del panel (no debería pasar) se usa la del navegador.
        if (!modalEl || !window.bootstrap) {
            if (window.confirm('¿Eliminar ' + texto + '? Esta acción no se puede deshacer.')) enviar(boton.dataset.accion);
            return;
        }

        const cuerpo = document.getElementById('paModalCuerpo');
        modalEl.querySelector('.modal-dialog').classList.remove('modal-lg');

        const cabecera = document.createElement('div');
        cabecera.className = 'pa-page-header';
        const titulo = document.createElement('h1');
        titulo.innerHTML = '<i class="fas fa-triangle-exclamation"></i> ';
        titulo.append('Eliminar ' + texto);
        cabecera.appendChild(titulo);

        const tarjeta = document.createElement('div');
        tarjeta.className = 'pa-card';
        const pregunta = document.createElement('p');
        pregunta.textContent = n === 1
            ? '¿Seguro que deseas eliminar est' + (terminacion === 'a' ? 'a ' : 'e ') + singular + '?'
            : '¿Seguro que deseas eliminar est' + (terminacion === 'a' ? 'as ' : 'os ') + texto + '?';

        const lista = document.createElement('ul');
        lista.className = 'pa-seleccion-lista';
        const MAX = 6;
        elegidas.slice(0, MAX).forEach(function (c) {
            const li = document.createElement('li');
            li.textContent = c.dataset.nombre || c.getAttribute('aria-label') || ('#' + c.value);
            lista.appendChild(li);
        });
        if (n > MAX) {
            const mas = document.createElement('li');
            mas.className = 'pa-seleccion-lista-mas';
            mas.textContent = 'y ' + (n - MAX) + ' más…';
            lista.appendChild(mas);
        }

        const aviso = document.createElement('p');
        aviso.className = 'pa-help';
        aviso.textContent = 'Esta acción no se puede deshacer.';

        const acciones = document.createElement('div');
        const si = document.createElement('button');
        si.type = 'button';
        si.className = 'pa-btn pa-btn-danger';
        si.innerHTML = '<i class="fas fa-trash"></i> Sí, eliminar';
        si.addEventListener('click', function () {
            si.disabled = true;
            enviar(boton.dataset.accion);
        });
        const no = document.createElement('button');
        no.type = 'button';
        no.className = 'pa-btn pa-btn-secondary';
        no.setAttribute('data-pa-cerrar', '');           // lo cierra el script de base_admin.html
        no.innerHTML = '<i class="fas fa-xmark"></i> Cancelar';
        acciones.append(si, ' ', no);

        tarjeta.append(pregunta, lista, aviso, acciones);
        cuerpo.replaceChildren(cabecera, tarjeta);
        bootstrap.Modal.getOrCreateInstance(modalEl).show();
    }

    botones.forEach(function (boton) {
        boton.addEventListener('click', function () {
            if (!marcadas().length) return;
            if (boton.hasAttribute('data-confirmar')) {
                confirmar(boton);
            } else {
                enviar(boton.dataset.accion);
            }
        });
    });

    // El navegador puede recordar casillas marcadas al volver atrás.
    actualizar();
    window.addEventListener('pageshow', actualizar);
})();
