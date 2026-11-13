// ═══════════════════════════════════════════════════════════════════════
// Vista previa del mapa de Google Maps en el formulario de salones
// (salon_form.html). El campo de dirección lleva
// data-mapa-vista-previa="<id del contenedor del mapa>"; al dejar de
// escribir un momento, el mapa de muestra se actualiza con lo escrito.
// Se escucha en el documento porque el formulario llega dentro de la
// ventana modal del panel después de cargar la página.
// ═══════════════════════════════════════════════════════════════════════
(function () {
    'use strict';

    let espera = null;

    document.addEventListener('input', function (e) {
        const campo = e.target.closest && e.target.closest('[data-mapa-vista-previa]');
        if (!campo) return;

        clearTimeout(espera);
        espera = setTimeout(function () {
            const contenedor = document.getElementById(campo.dataset.mapaVistaPrevia);
            if (!contenedor) return;
            const direccion = campo.value.trim();
            contenedor.hidden = !direccion;
            if (!direccion) return;
            const mapa = contenedor.querySelector('iframe');
            mapa.src = 'https://www.google.com/maps?q=' + encodeURIComponent(direccion) + '&output=embed';
        }, 700);
    });
})();
