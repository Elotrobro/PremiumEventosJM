// Galería: carga progresiva de fotos al hacer scroll, acordeón de tipos
// de evento y visor de fotos a pantalla completa.

document.addEventListener('DOMContentLoaded', function () {

    // ── Carga progresiva ────────────────────────────────────────────
    // Cada foto llega al navegador con opacity:0 (ver galeria.css). El
    // IntersectionObserver le pone .is-visible cuando el scroll la acerca
    // a la pantalla, y .is-loaded cuando el archivo termina de bajar (lo
    // que apaga el esqueleto con brillo). El resultado es que las fotos
    // se van "revelando" a medida que se baja por la página.
    const fotos = document.querySelectorAll('.ga-foto');

    const marcarCargada = (foto) => foto.classList.add('is-loaded');

    fotos.forEach(foto => {
        const img = foto.querySelector('img');
        if (img.complete) {
            marcarCargada(foto);
        } else {
            img.addEventListener('load', () => marcarCargada(foto));
            // Si una foto falla (archivo movido o borrado), se apaga el
            // esqueleto igual para no dejar el hueco parpadeando.
            img.addEventListener('error', () => marcarCargada(foto));
        }
    });

    if ('IntersectionObserver' in window) {
        const observador = new IntersectionObserver((entradas, obs) => {
            // El escalonado hace que las fotas de una misma fila no
            // aparezcan todas de golpe, sino uno detrás de otra.
            entradas.filter(e => e.isIntersecting).forEach((entrada, posicion) => {
                entrada.target.style.transitionDelay = `${Math.min(posicion, 6) * 70}ms`;
                entrada.target.classList.add('is-visible');
                obs.unobserve(entrada.target);
            });
        }, {
            // Se dispara un poco antes de que la foto entre en pantalla,
            // para que la transición no se vea a medias.
            rootMargin: '0px 0px -12% 0px',
            threshold: 0.05,
        });
        fotos.forEach(foto => observador.observe(foto));
    } else {
        fotos.forEach(foto => foto.classList.add('is-visible'));
    }

    // ── Acordeón de tipos de evento ─────────────────────────────────
    document.querySelectorAll('.ga-grupo-head').forEach(boton => {
        boton.addEventListener('click', () => {
            const grupo = boton.closest('.ga-grupo');
            const abierto = grupo.classList.toggle('is-open');
            boton.setAttribute('aria-expanded', abierto ? 'true' : 'false');
        });
    });

    // ── Visor de fotos a pantalla completa ──────────────────────────
    const visor = document.getElementById('gaVisor');
    if (!visor || !fotos.length) return;

    const visorImg = visor.querySelector('img');
    const contador = visor.querySelector('.ga-visor-contador');
    const urls = Array.from(fotos, foto => foto.querySelector('img').src);
    let actual = 0;

    function mostrar(indice) {
        // El módulo permite pasar de la última a la primera y al revés.
        actual = (indice + urls.length) % urls.length;
        visorImg.src = urls[actual];
        contador.textContent = `${actual + 1} / ${urls.length}`;
    }

    function abrir(indice) {
        mostrar(indice);
        visor.classList.add('is-open');
        document.body.style.overflow = 'hidden';
    }

    function cerrar() {
        visor.classList.remove('is-open');
        document.body.style.overflow = '';
    }

    fotos.forEach((foto, indice) => {
        foto.addEventListener('click', () => abrir(indice));
        foto.addEventListener('keydown', (evento) => {
            if (evento.key === 'Enter' || evento.key === ' ') {
                evento.preventDefault();
                abrir(indice);
            }
        });
    });

    visor.querySelector('.ga-visor-cerrar').addEventListener('click', cerrar);
    visor.querySelector('.ga-visor-prev').addEventListener('click', () => mostrar(actual - 1));
    visor.querySelector('.ga-visor-next').addEventListener('click', () => mostrar(actual + 1));

    // Clic en el fondo oscuro (fuera de la foto y de los botones) cierra
    visor.addEventListener('click', (evento) => {
        if (evento.target === visor) cerrar();
    });

    document.addEventListener('keydown', (evento) => {
        if (!visor.classList.contains('is-open')) return;
        if (evento.key === 'Escape') cerrar();
        if (evento.key === 'ArrowRight') mostrar(actual + 1);
        if (evento.key === 'ArrowLeft') mostrar(actual - 1);
    });
});
