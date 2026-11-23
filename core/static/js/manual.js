// ═══════════════════════════════════════════════════════════════════════
// Manual de usuario del panel — Premium Eventos JM
//
// Solo se carga para administrador y empleado (ver base.html). El botón
// "Manual de usuario" de la burbuja "JM" abre la ventana #jmManual; la
// primera vez trae el contenido de /panel-admin/manual/
// (panel_admin/templates/panel_admin/manual/manual.html).
//
// Dentro del manual:
//   - índice de capítulos, botones Anterior / Siguiente y flechas ← →
//   - buscador que filtra los capítulos del índice
//   - barra de avance y "Capítulo N de M"
//   - recuerda el último capítulo visto (solo en este navegador)
//   - cada capítulo tiene una ilustración donde un cursor hace clic en el
//     botón importante; aquí se calcula a dónde debe moverse.
// Las animaciones están en core/static/css/manual.css.
// ═══════════════════════════════════════════════════════════════════════
(function () {
  "use strict";

  const boton = document.getElementById("jmManualBtn");
  const ventana = document.getElementById("jmManual");
  if (!boton || !ventana) return;

  const CLAVE_CAPITULO = "jmManualCapitulo";
  let cargado = false;
  let cargando = false;
  let capitulos = [];
  let actual = 0;

  function leerGuardado() {
    try { return window.localStorage.getItem(CLAVE_CAPITULO); } catch (e) { return null; }
  }

  function guardar(id) {
    try { window.localStorage.setItem(CLAVE_CAPITULO, id); } catch (e) { /* modo privado: no pasa nada */ }
  }

  // ── Cursor de las ilustraciones: va hasta el elemento .mu-demo-objetivo ──
  function apuntarCursor(demo) {
    const objetivo = demo.querySelector(".mu-demo-objetivo");
    const cursor = demo.querySelector(".mu-demo-cursor");
    if (!objetivo || !cursor) return;
    const caja = demo.getBoundingClientRect();
    const meta = objetivo.getBoundingClientRect();
    if (!caja.width) return; // todavía oculto
    cursor.style.setProperty("--cx", (meta.left - caja.left + meta.width * 0.6) + "px");
    cursor.style.setProperty("--cy", (meta.top - caja.top + meta.height * 0.55) + "px");
  }

  function apuntarCursores() {
    const visible = capitulos[actual];
    if (visible) visible.querySelectorAll(".mu-demo").forEach(apuntarCursor);
  }

  // Lleva el capítulo activo a la vista dentro del índice (vertical en
  // computador, fila deslizable en celular). No se usa scrollIntoView
  // porque también movería la ventana del manual y la descuadraría.
  function mostrarEnIndice(boton) {
    const lista = boton.parentElement;
    const caja = lista.getBoundingClientRect();
    const b = boton.getBoundingClientRect();
    if (lista.scrollWidth > lista.clientWidth) {
      if (b.left < caja.left) lista.scrollLeft -= caja.left - b.left + 12;
      else if (b.right > caja.right) lista.scrollLeft += b.right - caja.right + 12;
    }
    const indice = ventana.querySelector(".mu-indice");
    if (indice && indice.scrollHeight > indice.clientHeight) {
      const ci = indice.getBoundingClientRect();
      if (b.top < ci.top) indice.scrollTop -= ci.top - b.top + 12;
      else if (b.bottom > ci.bottom) indice.scrollTop += b.bottom - ci.bottom + 12;
    }
  }

  // ── Mostrar un capítulo ───────────────────────────────────────────
  function mostrar(indice, { enfocar = false } = {}) {
    if (!capitulos.length) return;
    actual = Math.max(0, Math.min(indice, capitulos.length - 1));

    capitulos.forEach((cap, i) => {
      const activo = i === actual;
      cap.hidden = !activo;
      cap.classList.remove("mu-entrando");
      if (activo) {
        void cap.offsetWidth;          // reinicia la animación de entrada
        cap.classList.add("mu-entrando");
      }
    });

    const id = capitulos[actual].dataset.capitulo;
    ventana.querySelectorAll("[data-ir]").forEach((b) => {
      const es = b.dataset.ir === id;
      b.classList.toggle("activo", es);
      if (es) {
        b.setAttribute("aria-current", "step");
        mostrarEnIndice(b);
      } else {
        b.removeAttribute("aria-current");
      }
    });

    const total = capitulos.length;
    const progreso = ventana.querySelector(".mu-progreso");
    if (progreso) {
      progreso.querySelector("span").style.width = ((actual + 1) / total * 100) + "%";
      progreso.setAttribute("aria-valuenow", String(actual + 1));
      progreso.setAttribute("aria-valuemax", String(total));
    }
    const contador = ventana.querySelector(".mu-contador");
    if (contador) contador.textContent = "Capítulo " + (actual + 1) + " de " + total;

    const anterior = ventana.querySelector("[data-mu-anterior]");
    const siguiente = ventana.querySelector("[data-mu-siguiente]");
    if (anterior) anterior.disabled = actual === 0;
    if (siguiente) {
      const ultimo = actual === total - 1;
      siguiente.innerHTML = ultimo
        ? 'Terminar <i class="fas fa-check"></i>'
        : 'Siguiente <i class="fas fa-arrow-right"></i>';
    }

    const contenido = ventana.querySelector(".mu-contenido");
    if (contenido) {
      contenido.scrollTop = 0;
      if (enfocar) contenido.focus({ preventScroll: true });
    }

    guardar(id);
    requestAnimationFrame(apuntarCursores);
  }

  function irA(id) {
    const i = capitulos.findIndex((c) => c.dataset.capitulo === id);
    if (i > -1) mostrar(i, { enfocar: true });
  }

  // ── Buscador del índice ───────────────────────────────────────────
  function quitarTildes(texto) {
    return texto.normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase();
  }

  function filtrar(texto) {
    const busca = quitarTildes(texto.trim());
    let visibles = 0;
    ventana.querySelectorAll("[data-ir]").forEach((b) => {
      const cap = capitulos.find((c) => c.dataset.capitulo === b.dataset.ir);
      const coincide = !busca || quitarTildes((cap ? cap.textContent : "") + " " + b.textContent).includes(busca);
      b.hidden = !coincide;
      if (coincide) visibles++;
    });
    const aviso = ventana.querySelector(".mu-sin-resultados");
    if (aviso) aviso.hidden = visibles > 0;
  }

  // ── Preparar el contenido una vez cargado ─────────────────────────
  function preparar() {
    capitulos = Array.from(ventana.querySelectorAll(".mu-capitulo"));

    ventana.addEventListener("click", (e) => {
      const ir = e.target.closest("[data-ir]");
      if (ir) { irA(ir.dataset.ir); return; }
      if (e.target.closest("[data-mu-anterior]")) { mostrar(actual - 1, { enfocar: true }); return; }
      if (e.target.closest("[data-mu-siguiente]")) {
        if (actual === capitulos.length - 1) ventana.close();
        else mostrar(actual + 1, { enfocar: true });
        return;
      }
      if (e.target.closest("[data-mu-cerrar]")) { ventana.close(); return; }
      // Clic en el fondo oscuro (fuera del recuadro): cerrar.
      if (e.target === ventana) {
        const r = ventana.getBoundingClientRect();
        if (e.clientX < r.left || e.clientX > r.right || e.clientY < r.top || e.clientY > r.bottom) ventana.close();
      }
    });

    ventana.addEventListener("keydown", (e) => {
      const escribiendo = e.target.matches("input, textarea, select") || e.target.isContentEditable;
      if (escribiendo) return;
      if (e.key === "ArrowRight") { e.preventDefault(); mostrar(actual + 1, { enfocar: true }); }
      if (e.key === "ArrowLeft") { e.preventDefault(); mostrar(actual - 1, { enfocar: true }); }
    });

    const buscador = ventana.querySelector("[data-mu-buscar]");
    if (buscador) {
      buscador.addEventListener("input", () => filtrar(buscador.value));
      buscador.addEventListener("keydown", (e) => {
        // Enter abre el primer capítulo que coincide.
        if (e.key !== "Enter") return;
        e.preventDefault();
        const primero = Array.from(ventana.querySelectorAll("[data-ir]")).find((b) => !b.hidden);
        if (primero) irA(primero.dataset.ir);
      });
    }

    window.addEventListener("resize", () => { if (ventana.open) apuntarCursores(); });

    const guardado = leerGuardado();
    const inicial = capitulos.findIndex((c) => c.dataset.capitulo === guardado);
    mostrar(inicial > -1 ? inicial : 0);
  }

  async function cargar() {
    if (cargado || cargando) return cargado;
    cargando = true;
    try {
      const resp = await fetch(boton.dataset.url, {
        credentials: "same-origin",
        headers: { "X-Requested-With": "fetch" },
      });
      if (!resp.ok || resp.redirected) throw new Error("sin permiso o sin sesión");
      ventana.innerHTML = await resp.text();
      cargado = true;
      preparar();
    } catch (e) {
      ventana.close();
      if (window.notificar) {
        window.notificar("No se pudo abrir el manual. Recarga la página e intenta de nuevo.", "error", { titulo: "Manual de usuario" });
      }
    } finally {
      cargando = false;
    }
    return cargado;
  }

  async function abrir() {
    // Cierra el panel de opciones de la burbuja antes de abrir el manual.
    const widget = document.getElementById("jmWidget");
    const toggle = document.getElementById("jmWidgetToggle");
    if (widget) widget.classList.remove("is-open");
    if (toggle) toggle.setAttribute("aria-expanded", "false");

    if (!ventana.open) ventana.showModal();
    if (await cargar()) {
      const contenido = ventana.querySelector(".mu-contenido");
      if (contenido) contenido.focus({ preventScroll: true });
      requestAnimationFrame(apuntarCursores);
    }
  }

  boton.addEventListener("click", (e) => {
    e.stopPropagation();
    abrir();
  });

  // Al cerrar, el foco vuelve al botón "JM".
  ventana.addEventListener("close", () => {
    const toggle = document.getElementById("jmWidgetToggle");
    if (toggle) toggle.focus({ preventScroll: true });
  });
})();
