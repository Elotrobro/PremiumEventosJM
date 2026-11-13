// ═══════════════════════════════════════════════════════════════════════
// Búsqueda progresiva de los listados del panel (Usuarios y Salones).
//
// El formulario del buscador lleva data-busqueda-progresiva. Mientras se
// escribe (o al cambiar un filtro de lista), se pide la misma página con
// los nuevos parámetros y se reemplazan solo las zonas marcadas con
// data-busqueda-zona="…" (resultados, conteo y botón Limpiar). Así el
// campo de búsqueda no pierde el foco ni lo escrito, y la dirección de
// la página queda con ?q=… por si se recarga o se comparte.
// La búsqueda en sí la sigue haciendo el servidor (filtra y pagina), igual
// que al pulsar "Buscar"; sin JavaScript el formulario funciona como antes.
// ═══════════════════════════════════════════════════════════════════════
(function () {
    'use strict';

    const form = document.querySelector('form[data-busqueda-progresiva]');
    if (!form) return;

    const ESPERA_MS = 300;   // pausa al escribir antes de buscar
    let espera = null;
    let peticion = null;     // para cancelar una búsqueda vieja si llega otra letra

    function urlDeBusqueda() {
        const parametros = new URLSearchParams(new FormData(form));
        parametros.delete('page');   // una búsqueda nueva siempre empieza en la página 1
        const base = form.getAttribute('action') || window.location.pathname;
        return base + '?' + parametros.toString();
    }

    // Los <script> que llegan dentro del HTML nuevo (ej. el selector
    // "Registros por página" de _paginacion.html) no se ejecutan solos.
    function activarScripts(zona) {
        zona.querySelectorAll('script').forEach(function (viejo) {
            const nuevo = document.createElement('script');
            nuevo.textContent = viejo.textContent;
            viejo.replaceWith(nuevo);
        });
    }

    async function buscar() {
        const url = urlDeBusqueda();
        const resultados = document.querySelector('[data-busqueda-zona="resultados"]');

        if (peticion) peticion.abort();
        peticion = new AbortController();
        if (resultados) resultados.classList.add('pa-buscando');

        let html;
        try {
            const resp = await fetch(url, { credentials: 'same-origin', signal: peticion.signal });
            if (!resp.ok || resp.redirected) {
                window.location.href = url;   // ej. la sesión venció: se navega normal
                return;
            }
            html = await resp.text();
        } catch (e) {
            if (e.name !== 'AbortError' && resultados) resultados.classList.remove('pa-buscando');
            return;
        }

        const nuevo = new DOMParser().parseFromString(html, 'text/html');
        document.querySelectorAll('[data-busqueda-zona]').forEach(function (zona) {
            const reemplazo = nuevo.querySelector('[data-busqueda-zona="' + zona.dataset.busquedaZona + '"]');
            if (!reemplazo) return;
            const importada = document.importNode(reemplazo, true);
            zona.replaceWith(importada);
            activarScripts(importada);
        });

        window.history.replaceState(null, '', url);
        // seleccion.js vuelve a contar las casillas de la lista nueva.
        document.dispatchEvent(new CustomEvent('pa:listado-actualizado'));
    }

    function programar() {
        clearTimeout(espera);
        espera = setTimeout(buscar, ESPERA_MS);
    }

    form.addEventListener('input', function (e) {
        if (e.target.matches('input[type="search"], input[type="text"]')) programar();
    });

    form.addEventListener('change', function (e) {
        if (e.target.matches('select')) {
            clearTimeout(espera);
            buscar();
        }
    });

    // "Buscar"/"Aplicar" y la tecla Enter también buscan sin recargar.
    form.addEventListener('submit', function (e) {
        e.preventDefault();
        clearTimeout(espera);
        buscar();
    });
})();
