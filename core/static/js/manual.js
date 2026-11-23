// ═══════════════════════════════════════════════════════════════════════
// Manual de usuario del panel — "Centro de ayuda" de Premium Eventos JM
//
// Se carga solo para administrador y empleado: en el sitio (base.html,
// opción "Manual de usuario" de la burbuja "JM") y en el panel
// (base_admin.html, botón "Manual" de la barra superior). Cualquier botón
// con data-abrir-manual y data-url abre la ventana #jmManual; la primera
// vez trae el contenido de /panel-admin/manual/
// (panel_admin/templates/panel_admin/manual/manual.html).
//
// Dentro del manual:
//   - Portada con una tarjeta por sección y los recorridos en vivo.
//   - Cada sección se lee de corrido: sus módulos van uno debajo del otro,
//     el índice lateral marca dónde vas y el contenido aparece animado al
//     bajar (no hay que pasar página por página).
//   - Buscador en todo el manual, sin importar tildes ni mayúsculas.
//   - "Muéstrame en vivo": abre esa pantalla del panel y la recorre
//     señalando los botones reales (core/static/js/recorrido.js).
//   - Recuerda la última sección y tema vistos (solo en este navegador).
// Las animaciones están en core/static/css/manual.css.
// ═══════════════════════════════════════════════════════════════════════
(function () {
  "use strict";

  const ventana = document.getElementById("jmManual");
  const botones = document.querySelectorAll("[data-abrir-manual]");
  if (!ventana || !botones.length) return;

  const CLAVE = "jmManualLugar";
  let raiz = null;          // .mu
  let cargado = false;
  let cargando = null;
  let observadorEspia = null;
  let observadorRevelar = null;
  let seccionActual = null;

  // ── Utilidades ────────────────────────────────────────────────────
  function leerLugar() {
    try { return JSON.parse(window.localStorage.getItem(CLAVE) || "null"); } catch (e) { return null; }
  }

  function guardarLugar(seccion, modulo) {
    try { window.localStorage.setItem(CLAVE, JSON.stringify({ seccion, modulo })); } catch (e) { /* modo privado */ }
  }

  function normalizar(texto) {
    return (texto || "").normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase();
  }

  function cerrarBurbuja() {
    const widget = document.getElementById("jmWidget");
    const toggle = document.getElementById("jmWidgetToggle");
    if (widget) widget.classList.remove("is-open");
    if (toggle) toggle.setAttribute("aria-expanded", "false");
  }

  // ── Cursor de las ilustraciones: va hasta su .mu-demo-objetivo ─────
  function apuntarCursor(demo) {
    const objetivo = demo.querySelector(".mu-demo-objetivo");
    const cursor = demo.querySelector(".mu-demo-cursor");
    if (!objetivo || !cursor) return;
    const caja = demo.getBoundingClientRect();
    const meta = objetivo.getBoundingClientRect();
    if (!caja.width) return;
    cursor.style.setProperty("--cx", (meta.left - caja.left + meta.width * 0.6) + "px");
    cursor.style.setProperty("--cy", (meta.top - caja.top + meta.height * 0.55) + "px");
  }

  // ── Vistas: portada, resultados de búsqueda o una sección ──────────
  function mostrarVista(nombre, seccion) {
    raiz.dataset.vista = nombre;
    raiz.querySelectorAll("[data-mu-vista]").forEach((v) => {
      v.hidden = !(v.dataset.muVista === nombre && (nombre !== "seccion" || v === seccion));
    });
    const migas = raiz.querySelector(".mu-migas-seccion");
    if (migas) {
      migas.hidden = nombre !== "seccion";
      if (seccion) migas.querySelector("b").textContent = seccion.dataset.titulo;
    }
  }

  function irAPortada() {
    seccionActual = null;
    const buscador = raiz.querySelector("[data-mu-buscar]");
    if (buscador) buscador.value = "";
    mostrarVista("portada");
    prepararContinuar();
    const portada = raiz.querySelector(".mu-portada");
    portada.scrollTop = 0;
    portada.classList.remove("mu-entrando");
    void portada.offsetWidth;
    portada.classList.add("mu-entrando");
  }

  function irASeccion(id, moduloId, { suave = false } = {}) {
    const seccion = raiz.querySelector('.mu-seccion[data-seccion="' + id + '"]');
    if (!seccion) return;
    seccionActual = seccion;
    mostrarVista("seccion", seccion);
    seccion.classList.remove("mu-entrando");
    void seccion.offsetWidth;
    seccion.classList.add("mu-entrando");

    const lectura = seccion.querySelector(".mu-lectura");
    vigilar(seccion);

    const modulo = moduloId && seccion.querySelector('.mu-modulo[data-modulo="' + moduloId + '"]');
    requestAnimationFrame(() => {
      if (modulo) {
        lectura.scrollTo({ top: modulo.offsetTop - 12, behavior: suave ? "smooth" : "auto" });
        modulo.classList.add("mu-destacado");
        setTimeout(() => modulo.classList.remove("mu-destacado"), 1600);
      } else {
        lectura.scrollTop = 0;
      }
      lectura.focus({ preventScroll: true });
      marcarModulo(seccion, (modulo || seccion.querySelector(".mu-modulo")).dataset.modulo);
    });
  }

  // ── Índice que sigue la lectura y animaciones al bajar ─────────────
  function marcarModulo(seccion, moduloId) {
    seccion.querySelectorAll("[data-ir-modulo]").forEach((b) => {
      const es = b.dataset.irModulo === moduloId;
      b.classList.toggle("activo", es);
      if (es) b.setAttribute("aria-current", "location"); else b.removeAttribute("aria-current");
    });
    guardarLugar(seccion.dataset.seccion, moduloId);
  }

  function vigilar(seccion) {
    if (observadorEspia) observadorEspia.disconnect();
    if (observadorRevelar) observadorRevelar.disconnect();
    const lectura = seccion.querySelector(".mu-lectura");

    if (!("IntersectionObserver" in window)) {
      seccion.querySelectorAll(".mu-revelar").forEach((el) => el.classList.add("visible"));
      return;
    }

    // Marca en el índice el módulo que está en la parte de arriba de la lectura.
    observadorEspia = new IntersectionObserver((entradas) => {
      const visibles = entradas.filter((e) => e.isIntersecting);
      if (visibles.length) marcarModulo(seccion, visibles[0].target.dataset.modulo);
    }, { root: lectura, rootMargin: "0px 0px -65% 0px" });
    seccion.querySelectorAll(".mu-modulo").forEach((m) => observadorEspia.observe(m));

    // Cada bloque aparece animado al entrar a la vista; las ilustraciones
    // solo se animan mientras se ven (así no gastan batería fuera de vista).
    observadorRevelar = new IntersectionObserver((entradas) => {
      entradas.forEach((e) => {
        if (e.isIntersecting) e.target.classList.add("visible");          // aparece una sola vez
        if (e.target.classList.contains("mu-demo")) {
          e.target.classList.toggle("mu-en-vista", e.isIntersecting);       // animación solo mientras se ve
          if (e.isIntersecting) apuntarCursor(e.target);
        }
      });
    }, { root: lectura, threshold: 0.12 });
    seccion.querySelectorAll(".mu-revelar").forEach((el) => observadorRevelar.observe(el));

    // Barra de avance de la sección.
    const avance = seccion.querySelector(".mu-avance span");
    if (avance && !lectura.dataset.avance) {
      lectura.dataset.avance = "1";
      lectura.addEventListener("scroll", () => {
        const total = lectura.scrollHeight - lectura.clientHeight;
        avance.style.width = (total > 0 ? (lectura.scrollTop / total) * 100 : 100) + "%";
      }, { passive: true });
    }
  }

  // ── Buscador global ────────────────────────────────────────────────
  let indiceBusqueda = [];

  function armarIndice() {
    indiceBusqueda = Array.from(raiz.querySelectorAll(".mu-modulo")).map((m) => {
      const seccion = m.closest(".mu-seccion");
      return {
        modulo: m.dataset.modulo,
        titulo: m.dataset.titulo,
        seccion: seccion.dataset.seccion,
        seccionTitulo: seccion.dataset.titulo,
        texto: m.textContent.replace(/\s+/g, " ").trim(),
      };
    });
  }

  function fragmento(texto, termino) {
    const posicion = normalizar(texto).indexOf(termino);
    if (posicion < 0) return null;
    const inicio = Math.max(0, posicion - 50);
    const fin = Math.min(texto.length, posicion + termino.length + 70);
    return {
      antes: (inicio > 0 ? "…" : "") + texto.slice(inicio, posicion),
      encontrado: texto.slice(posicion, posicion + termino.length),
      despues: texto.slice(posicion + termino.length, fin) + (fin < texto.length ? "…" : ""),
    };
  }

  function buscar(texto) {
    const termino = normalizar(texto.trim());
    if (!termino) {
      if (seccionActual) irASeccion(seccionActual.dataset.seccion); else irAPortada();
      return;
    }
    mostrarVista("resultados");
    const caja = raiz.querySelector(".mu-resultados");
    caja.querySelector("[data-mu-termino]").textContent = texto.trim();
    const lista = caja.querySelector(".mu-resultados-lista");
    lista.replaceChildren();

    indiceBusqueda
      .filter((item) => normalizar(item.titulo + " " + item.texto).includes(termino))
      .forEach((item, i) => {
        const li = document.createElement("li");
        li.style.setProperty("--i", i);
        const boton = document.createElement("button");
        boton.type = "button";
        boton.dataset.irSeccion = item.seccion;
        boton.dataset.irModulo = item.modulo;

        const cabeza = document.createElement("span");
        cabeza.className = "mu-resultado-titulo";
        cabeza.textContent = item.titulo;
        const ruta = document.createElement("small");
        ruta.textContent = item.seccionTitulo;
        cabeza.appendChild(ruta);
        boton.appendChild(cabeza);

        // El fragmento se arma con nodos de texto (nunca con HTML).
        const trozo = fragmento(item.texto, termino);
        if (trozo) {
          const p = document.createElement("span");
          p.className = "mu-resultado-texto";
          const marca = document.createElement("mark");
          marca.textContent = trozo.encontrado;
          p.append(trozo.antes, marca, trozo.despues);
          boton.appendChild(p);
        }
        li.appendChild(boton);
        lista.appendChild(li);
      });

    caja.querySelector(".mu-sin-resultados").hidden = lista.children.length > 0;
  }

  // ── "Continuar donde quedaste" ─────────────────────────────────────
  function prepararContinuar() {
    const boton = raiz.querySelector("[data-mu-continuar]");
    const lugar = leerLugar();
    const modulo = lugar && raiz.querySelector('.mu-seccion[data-seccion="' + lugar.seccion + '"] .mu-modulo[data-modulo="' + lugar.modulo + '"]');
    boton.hidden = !modulo;
    if (modulo) {
      boton.dataset.seccion = lugar.seccion;
      boton.dataset.modulo = lugar.modulo;
      boton.querySelector("b").textContent = modulo.dataset.titulo;
    }
  }

  // ── "Muéstrame en vivo" ────────────────────────────────────────────
  function enVivo(boton) {
    const destino = new URL(boton.dataset.url, window.location.href);
    const id = boton.dataset.recorrido;
    // Si ya estamos en esa pantalla del panel, el recorrido empieza aquí mismo.
    if (window.PremiumRecorrido && destino.pathname === window.location.pathname) {
      ventana.close();
      window.PremiumRecorrido.iniciar(id);
      return;
    }
    destino.searchParams.set("recorrido", id);
    window.location.href = destino.pathname + destino.search;
  }

  // ── Preparar el contenido una vez cargado ──────────────────────────
  function preparar() {
    raiz = ventana.querySelector(".mu");

    // Bloques que aparecen animados al bajar.
    raiz.querySelectorAll(".mu-modulo > *, .mu-seccion-cabecera, .mu-siguiente-seccion").forEach((el) => {
      el.classList.add("mu-revelar");
    });
    armarIndice();

    ventana.addEventListener("click", (e) => {
      const t = e.target;
      const vivo = t.closest("[data-recorrido]");
      if (vivo) { enVivo(vivo); return; }
      const continuar = t.closest("[data-mu-continuar]");
      if (continuar) { irASeccion(continuar.dataset.seccion, continuar.dataset.modulo); return; }
      const aSeccion = t.closest("[data-ir-seccion]");
      if (aSeccion) {
        const buscador = raiz.querySelector("[data-mu-buscar]");
        if (buscador) buscador.value = "";
        irASeccion(aSeccion.dataset.irSeccion, aSeccion.dataset.irModulo);
        return;
      }
      const aModulo = t.closest("[data-ir-modulo]");
      if (aModulo && seccionActual) { irASeccion(seccionActual.dataset.seccion, aModulo.dataset.irModulo, { suave: true }); return; }
      if (t.closest("[data-mu-portada]")) { irAPortada(); return; }
      if (t.closest("[data-mu-cerrar]")) { ventana.close(); return; }
      // Clic en el fondo oscuro (fuera del recuadro): cerrar.
      if (t === ventana) {
        const r = ventana.getBoundingClientRect();
        if (e.clientX < r.left || e.clientX > r.right || e.clientY < r.top || e.clientY > r.bottom) ventana.close();
      }
    });

    const buscador = raiz.querySelector("[data-mu-buscar]");
    let espera = null;
    buscador.addEventListener("input", () => {
      clearTimeout(espera);
      espera = setTimeout(() => buscar(buscador.value), 150);
    });
    buscador.addEventListener("keydown", (e) => {
      if (e.key === "Enter") {
        e.preventDefault();
        const primero = raiz.querySelector(".mu-resultados-lista button");
        if (primero) primero.click();
      }
    });

    window.addEventListener("resize", () => {
      if (ventana.open && seccionActual) seccionActual.querySelectorAll(".mu-demo.mu-en-vista").forEach(apuntarCursor);
    });

    irAPortada();
  }

  async function cargar(url) {
    if (cargado) return true;
    if (!cargando) {
      cargando = (async () => {
        try {
          const resp = await fetch(url, { credentials: "same-origin", headers: { "X-Requested-With": "fetch" } });
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
          cargando = null;
        }
        return cargado;
      })();
    }
    return cargando;
  }

  async function abrir(boton) {
    cerrarBurbuja();
    if (!ventana.open) ventana.showModal();
    if (await cargar(boton.dataset.url)) {
      if (boton.dataset.seccion) irASeccion(boton.dataset.seccion, boton.dataset.modulo);
      else if (raiz.dataset.vista === "portada") prepararContinuar();
    }
  }

  botones.forEach((boton) => {
    boton.addEventListener("click", (e) => {
      e.stopPropagation();
      abrir(boton);
    });
  });

  // Desde el recorrido en vivo: "Volver al manual" abre el tema que se estaba viendo.
  window.PremiumManual = {
    abrir(seccion, modulo) {
      const boton = botones[0];
      abrir({ dataset: { url: boton.dataset.url, seccion: seccion || "", modulo: modulo || "" } });
    },
  };

  // Al cerrar, el foco vuelve al botón con el que se abrió.
  ventana.addEventListener("close", () => {
    const origen = document.getElementById("jmWidgetToggle") || botones[0];
    if (origen) origen.focus({ preventScroll: true });
  });
})();
