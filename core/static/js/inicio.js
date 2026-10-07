// ═══════════════════════════════════════════════════════════════════════
// Portada de inicio (hero) — core/templates/inicio.html + css/inicio.css
//
//   1) Aparición suave del texto (las transiciones de 1 s están en el CSS;
//      aquí solo se agrega la clase .listo para dispararlas).
//   2) Fotos de fondo que se desvanecen una tras otra cada 6 segundos.
//      Los puntos de abajo permiten elegir una foto.
//   3) El alto de la portada se ajusta al alto real del menú.
// No toca la ventana de cotización: el botón "Cotizar mi evento" llama a
// abrirModalCotizacion() de modal.js, igual que antes.
// ═══════════════════════════════════════════════════════════════════════

document.addEventListener("DOMContentLoaded", () => {
  const hero = document.getElementById("heroInicio");
  if (!hero) return;

  const fondos = Array.from(hero.querySelectorAll(".hero-fondo"));
  const puntos = Array.from(hero.querySelectorAll(".hero-punto"));
  const SEGUNDOS_POR_FOTO = 6;
  let actual = 0;
  let temporizador = null;

  // ── 3) Alto del menú ─────────────────────────────────────────────────
  const nav = document.querySelector("nav.navbar");
  const ajustarAlto = () => {
    if (nav) hero.style.setProperty("--alto-nav", nav.offsetHeight + "px");
  };
  ajustarAlto();
  window.addEventListener("resize", ajustarAlto);

  // ── 1) Texto ─────────────────────────────────────────────────────────
  // Se espera un cuadro para que el navegador pinte el estado inicial y la
  // transición se vea (si no, el texto aparecería de golpe).
  requestAnimationFrame(() => requestAnimationFrame(() => hero.classList.add("listo")));

  // ── 2) Fotos ─────────────────────────────────────────────────────────
  // Las fotos 2 en adelante se cargan cuando la página ya terminó de cargar,
  // para que la primera aparezca lo más rápido posible.
  const cargarResto = () => {
    fondos.forEach((img) => {
      if (img.dataset.src) {
        img.src = img.dataset.src;
        delete img.dataset.src;
      }
    });
  };
  if (document.readyState === "complete") cargarResto();
  else window.addEventListener("load", cargarResto);

  const mostrar = (indice) => {
    const siguiente = (indice + fondos.length) % fondos.length;
    if (fondos[siguiente].dataset.src) cargarResto();
    fondos[actual].classList.remove("activo");
    puntos[actual]?.classList.remove("activo");
    puntos[actual]?.setAttribute("aria-selected", "false");
    fondos[siguiente].classList.add("activo");
    puntos[siguiente]?.classList.add("activo");
    puntos[siguiente]?.setAttribute("aria-selected", "true");
    actual = siguiente;
  };

  const iniciar = () => {
    clearInterval(temporizador);
    temporizador = setInterval(() => mostrar(actual + 1), SEGUNDOS_POR_FOTO * 1000);
  };

  puntos.forEach((punto, i) => {
    punto.setAttribute("role", "tab");
    punto.setAttribute("aria-selected", i === 0 ? "true" : "false");
    punto.addEventListener("click", () => {
      mostrar(i);
      iniciar(); // vuelve a contar los 6 segundos desde el clic
    });
  });

  // Si la pestaña no está visible, se pausa (no gasta datos ni batería).
  document.addEventListener("visibilitychange", () => {
    if (document.hidden) clearInterval(temporizador);
    else iniciar();
  });

  if (fondos.length > 1) iniciar();
});
