// ═══════════════════════════════════════════════════════════════════════
// Recorrido guiado en vivo del panel — Premium Eventos JM
//
// Se carga en todas las pantallas del panel (base_admin.html). El botón
// "Muéstrame en vivo" del manual (core/static/js/manual.js) abre la
// pantalla del módulo con ?recorrido=<id>, o llama a
// PremiumRecorrido.iniciar(id) si ya se está en ella.
//
// El recorrido oscurece la pantalla y deja iluminado, uno por uno, el
// elemento REAL del panel que se explica (botones, buscadores, tablas…),
// con un globo que dice qué hace. Los pasos cuyo elemento no existe en
// pantalla (ej. "Eliminar" para un empleado, o una lista vacía) se
// saltan solos.
//
// Para agregar o cambiar pasos: edita RECORRIDOS. Cada paso tiene:
//   donde: selector CSS del elemento (o lista de selectores; se usa el
//          primero que esté visible). Sin "donde", el globo sale centrado.
//   titulo, texto: lo que dice el globo.
// Estilos y animaciones en core/static/css/recorrido.css.
// ═══════════════════════════════════════════════════════════════════════
(function () {
  "use strict";

  const RECORRIDOS = {
    inicio: {
      titulo: "Recorrido general del panel",
      seccion: "primeros-pasos", modulo: "inicio",
      pasos: [
        { titulo: "¡Bienvenido al panel!", texto: "Te mostraremos dónde está cada cosa. Usa Siguiente o las flechas del teclado; Esc para salir cuando quieras." },
        { donde: ".pa-sidebar", titulo: "Menú de módulos", texto: "Desde aquí entras a cada módulo. El que estás viendo queda resaltado." },
        { donde: ".pa-rol-tag", titulo: "Tu rol", texto: "Te recuerda si entraste como Administrador o Empleado. Algunas acciones (eliminar, validar cotizaciones, cambiar precios) son solo del administrador." },
        { donde: "#paManualBtn", titulo: "Manual siempre a mano", texto: "Abre el centro de ayuda desde cualquier pantalla del panel." },
        { donde: ".pa-stats", titulo: "Totales del negocio", texto: "Usuarios, cotizaciones (y cuántas están pendientes), mensajes e ítems del catálogo." },
        { donde: ".pa-dias-opciones", titulo: "Período de novedades", texto: "Elige si quieres ver lo de los últimos 7, 14 o 30 días." },
        { donde: ".pa-novedades", titulo: "Novedades", texto: "Las cotizaciones que llegaron y los eventos que se vienen. Haz clic en una para ver su detalle completo." },
      ],
    },
    usuarios: {
      titulo: "Usuarios",
      seccion: "personas", modulo: "usuarios",
      pasos: [
        { donde: ".pa-page-header a[href$='/usuarios/nuevo/']", titulo: "Crear un usuario", texto: "Abre el formulario para crear una cuenta nueva." },
        { donde: "#buscarUsuario", titulo: "Buscador progresivo", texto: "Escribe parte del nombre o del correo: la lista se filtra mientras escribes." },
        { donde: "#paFormSeleccion", titulo: "Selección múltiple", texto: "Marca varias casillas y elimina en grupo. Shift + clic marca un rango." },
        { donde: "[data-busqueda-zona='resultados']", titulo: "La lista de usuarios", texto: "Nombre, correo, rol y último acceso. Los clientes sin cotizar muestran cuántos días les quedan antes de borrarse solos." },
        { donde: "a[title='Editar'][href*='/usuarios/']", titulo: "Editar (solo administrador)", texto: "El lápiz abre la edición del usuario." },
        { donde: ".pa-pagination-size", titulo: "Registros por página", texto: "Elige cuántos usuarios ver a la vez y muévete entre páginas." },
      ],
    },
    catalogo: {
      titulo: "Catálogo de decoración",
      seccion: "contenido", modulo: "catalogo",
      pasos: [
        { donde: ".pa-page-header a[href$='/catalogo/nuevo/']", titulo: "Nuevo ítem", texto: "Agrega un artículo con nombre, precio, categoría, unidad e imagen." },
        { donde: ".pa-view-controls", titulo: "Tabla o tarjetas", texto: "Cambia cómo ver el catálogo: en filas o en tarjetas con foto." },
        { donde: "#paFormSeleccion", titulo: "Acciones en grupo", texto: "Marca varios ítems y ponlos como disponibles o no disponibles de una vez." },
        { donde: [".pa-content .pa-table", ".pa-cotizaciones-grid"], titulo: "Tus ítems", texto: "Aquí está todo el inventario con su precio y si está disponible." },
        { donde: ["a[title='Editar'][href*='/catalogo/']", ".pa-cotizacion-card a[href*='/catalogo/'][href$='/editar/']"], titulo: "Editar", texto: "Cambia los datos o la foto de un ítem." },
      ],
    },
    galeria: {
      titulo: "Galería",
      seccion: "contenido", modulo: "galeria",
      pasos: [
        { donde: "form[action$='/galeria/subir/'] select", titulo: "1. Elige la categoría", texto: "Matrimonio, 15 años, Grados… Las fotos se guardan en esa categoría de la galería pública." },
        { donde: "form[action$='/galeria/subir/'] input[type='file']", titulo: "2. Selecciona las fotos", texto: "Puedes elegir varias a la vez con Ctrl o Shift + clic." },
        { donde: "form[action$='/galeria/subir/'] button[type='submit']", titulo: "3. Súbelas", texto: "Aparecen de inmediato en su categoría." },
        { donde: [".pa-galeria-grid", ".pa-content .pa-card:nth-of-type(2)"], titulo: "Fotos por categoría", texto: "Cada categoría muestra sus fotos. El administrador puede eliminarlas con la papelera o en grupo." },
      ],
    },
    salones: {
      titulo: "Salones",
      seccion: "contenido", modulo: "salones",
      pasos: [
        { donde: ".pa-page-header a[href$='/salones/nuevo/']", titulo: "Nuevo salón", texto: "Crea un salón con su información, su dirección para el mapa y varias fotos." },
        { donde: "#buscarSalon", titulo: "Buscar mientras escribes", texto: "Filtra por nombre o ubicación al instante." },
        { donde: "#estadoSalon", titulo: "Visibles u ocultos", texto: "Muestra solo los salones publicados en la página o los que están ocultos." },
        { donde: ".pa-view-controls", titulo: "Tabla o tarjetas", texto: "En tarjetas ves la foto de portada de cada salón." },
        { donde: "#paFormSeleccion", titulo: "Publicar u ocultar en grupo", texto: "Marca varios salones y cambia si se ven en la página, sin borrarlos." },
        { donde: ["a[title='Editar'][href*='/salones/']", ".pa-cotizacion-card a[href*='/salones/'][href$='/editar/']"], titulo: "Editar un salón", texto: "Cambia sus datos, agrega fotos o escribe la dirección: verás la vista previa del mapa." },
      ],
    },
    mensajes: {
      titulo: "Mensajes de contacto",
      seccion: "personas", modulo: "mensajes",
      pasos: [
        { donde: [".pa-content .pa-table", ".pa-content .pa-empty"], titulo: "Mensajes recibidos", texto: "Lo que escriben los visitantes en Contacto, con su correo y teléfono para responderles. Los más nuevos salen primero." },
        { donde: "a[title='Eliminar'][href*='/mensajes/']", titulo: "Eliminar (solo administrador)", texto: "Borra los mensajes que ya atendiste." },
      ],
    },
    testimonios: {
      titulo: "Testimonios",
      seccion: "personas", modulo: "testimonios",
      pasos: [
        { donde: ".pa-view-controls", titulo: "Tabla o tarjetas", texto: "Elige cómo leer las opiniones de los clientes." },
        { donde: "input[name='aprobado']", titulo: "Aprobado = publicado", texto: "Marca esta casilla para mostrar la opinión en la página de Testimonios; desmárcala para ocultarla. Se guarda al instante." },
        { donde: "#paFormSeleccion", titulo: "Varios a la vez", texto: "Publica u oculta varios testimonios de una vez." },
      ],
    },
    cotizaciones: {
      titulo: "Cotizaciones",
      seccion: "ventas", modulo: "cotizaciones",
      pasos: [
        { donde: "#estadoSelect", titulo: "Filtrar por estado", texto: "Pendiente, Aprobada, Rechazada, Completada o Pagado." },
        { donde: "#filtroSelect", titulo: "Filtrar por fecha", texto: "Siempre, último año, último mes o un rango de fechas." },
        { donde: ".pa-filtros button[type='submit']", titulo: "Aplicar", texto: "Muestra solo las cotizaciones que cumplen los filtros." },
        { donde: ".pa-view-controls", titulo: "Tabla o tarjetas", texto: "Las tarjetas muestran el código de seguimiento y los datos clave de cada evento." },
        { donde: ["a[href*='/cotizaciones/'][href$='/editar/']"], titulo: "Ver y validar", texto: "Abre el detalle completo. El administrador cambia aquí el estado; al aprobar o rechazar, el cliente recibe un correo." },
        { donde: ".pa-page-header a[href$='/historial/']", titulo: "Historial", texto: "Para reportes y el PDF, ve al historial." },
      ],
    },
    precios: {
      titulo: "Precios",
      seccion: "ventas", modulo: "precios",
      pasos: [
        { donde: ".pa-content .pa-card", titulo: "Precio por invitados", texto: "Cada fila es un tramo; entre dos tramos el precio se calcula en proporción." },
        { donde: ".pa-content .pa-card:has(.fa-concierge-bell)", titulo: "Precios de servicios", texto: "Se suman al precio base cuando el cliente los marca en la cotización." },
        { donde: ".pa-content form button[type='submit']", titulo: "Guardar (solo administrador)", texto: "Aplica los cambios a las cotizaciones nuevas; las que ya existen conservan su precio." },
      ],
    },
    historial: {
      titulo: "Historial y reportes",
      seccion: "ventas", modulo: "historial",
      pasos: [
        { donde: ".pa-filtros", titulo: "Filtros", texto: "Estado y fecha de la cotización, igual que en Cotizaciones." },
        { donde: ".pa-totales", titulo: "Totales", texto: "Cuántas cotizaciones hay con el filtro y cuánto suman." },
        { donde: "a[href*='/historial/pdf/']", titulo: "Descargar PDF", texto: "El reporte sale con el logo de la empresa y con los filtros que tienes aplicados." },
      ],
    },
  };

  let actual = null;      // { id, def, pasos, i }
  let capa = null;
  let foco = null;
  let globo = null;
  let seguimiento = null;

  // ── Utilidades ────────────────────────────────────────────────────
  function visible(el) {
    if (!el) return false;
    const r = el.getBoundingClientRect();
    const estilo = getComputedStyle(el);
    return r.width > 0 && r.height > 0 && estilo.visibility !== "hidden" && !el.closest("[hidden]");
  }

  function buscarElemento(donde) {
    if (!donde) return null;
    const lista = Array.isArray(donde) ? donde : [donde];
    for (const selector of lista) {
      let candidatos;
      try { candidatos = document.querySelectorAll(selector); } catch (e) { continue; } // selector no soportado
      for (const el of candidatos) {
        // Las casillas de Bootstrap son pequeñas: se ilumina su contenedor.
        const objetivo = el.matches("input[type='checkbox']") ? (el.closest(".form-check, .form-switch, td, label") || el) : el;
        if (visible(objetivo)) return objetivo;
      }
    }
    return null;
  }

  // ── Construir la capa del recorrido ────────────────────────────────
  function crearCapa() {
    capa = document.createElement("div");
    capa.className = "rc-capa";
    capa.setAttribute("role", "dialog");
    capa.setAttribute("aria-modal", "true");
    capa.setAttribute("aria-label", "Recorrido guiado");

    foco = document.createElement("div");
    foco.className = "rc-foco";

    globo = document.createElement("div");
    globo.className = "rc-globo";
    globo.innerHTML =
      '<div class="rc-globo-cabeza"><span class="rc-en-vivo"><span class="rc-punto"></span> En vivo</span>' +
      '<span class="rc-modulo"></span><button type="button" class="rc-salir" data-rc="salir" aria-label="Salir del recorrido"><i class="fas fa-xmark"></i></button></div>' +
      '<h4 class="rc-titulo"></h4><p class="rc-texto"></p>' +
      '<div class="rc-puntos" aria-hidden="true"></div>' +
      '<div class="rc-botones"><span class="rc-paso"></span>' +
      '<button type="button" class="rc-btn rc-btn-sec" data-rc="anterior"><i class="fas fa-arrow-left"></i> Anterior</button>' +
      '<button type="button" class="rc-btn" data-rc="siguiente">Siguiente <i class="fas fa-arrow-right"></i></button></div>';
    globo.setAttribute("aria-live", "polite");

    capa.append(foco, globo);
    document.body.appendChild(capa);

    capa.addEventListener("click", (e) => {
      const accion = e.target.closest("[data-rc]");
      if (!accion) return;
      const que = accion.dataset.rc;
      if (que === "salir") terminar();
      if (que === "anterior") ir(actual.i - 1, -1);
      if (que === "siguiente") ir(actual.i + 1, 1);
      if (que === "manual") {
        const def = actual.def;          // se guarda antes: terminar() borra "actual"
        terminar();
        if (window.PremiumManual) window.PremiumManual.abrir(def.seccion, def.modulo);
      }
      if (que === "terminar") terminar();
    });
  }

  function teclas(e) {
    if (!actual) return;
    if (e.key === "Escape") { e.preventDefault(); terminar(); }
    // (Enter no se usa aquí: ya activa el botón que tiene el foco.)
    if (e.key === "ArrowRight") { e.preventDefault(); ir(actual.i + 1, 1); }
    if (e.key === "ArrowLeft") { e.preventDefault(); ir(actual.i - 1, -1); }
  }

  // ── Posicionar el foco y el globo sobre el elemento ───────────────
  function colocar() {
    if (!actual) return;
    const paso = actual.pasos[actual.i];
    const el = paso.el;
    const margen = 8;
    const ancho = window.innerWidth;
    const alto = window.innerHeight;

    if (!el) {
      foco.classList.add("rc-foco-centro");
      foco.style.cssText = "";
      globo.classList.add("rc-globo-centro");
      globo.style.left = globo.style.top = "";
      return;
    }
    foco.classList.remove("rc-foco-centro");
    globo.classList.remove("rc-globo-centro");

    const r = el.getBoundingClientRect();
    foco.style.left = (r.left - margen) + "px";
    foco.style.top = (r.top - margen) + "px";
    foco.style.width = (r.width + margen * 2) + "px";
    foco.style.height = (r.height + margen * 2) + "px";

    // El globo va debajo del elemento si cabe; si no, arriba; si tampoco, al lado.
    const g = globo.getBoundingClientRect();
    let top = r.bottom + margen + 14;
    let lado = "abajo";
    if (top + g.height > alto - 10) {
      top = r.top - margen - 14 - g.height;
      lado = "arriba";
    }
    if (top < 10) {
      top = Math.min(Math.max(10, r.top), alto - g.height - 10);
      lado = "lado";
    }
    let left = r.left + r.width / 2 - g.width / 2;
    if (lado === "lado") left = r.right + margen + 14 + g.width < ancho ? r.right + margen + 14 : r.left - margen - 14 - g.width;
    left = Math.min(Math.max(10, left), ancho - g.width - 10);

    globo.style.left = left + "px";
    globo.style.top = top + "px";
    globo.dataset.lado = lado;
    // La flecha del globo apunta al centro del elemento.
    globo.style.setProperty("--flecha", Math.min(Math.max(18, r.left + r.width / 2 - left), g.width - 18) + "px");
  }

  function seguir() {
    cancelAnimationFrame(seguimiento);
    seguimiento = requestAnimationFrame(colocar);
  }

  // ── Mostrar un paso ───────────────────────────────────────────────
  function ir(indice, direccion) {
    if (!actual) return;
    if (indice >= actual.pasos.length) { final(); return; }
    if (indice < 0) return;

    actual.i = indice;
    const paso = actual.pasos[indice];
    const total = actual.pasos.length;

    globo.classList.remove("rc-final");
    globo.querySelector(".rc-modulo").textContent = actual.def.titulo;
    globo.querySelector(".rc-titulo").textContent = paso.titulo;
    globo.querySelector(".rc-texto").textContent = paso.texto;
    globo.querySelector(".rc-paso").textContent = "Paso " + (indice + 1) + " de " + total;
    const puntos = globo.querySelector(".rc-puntos");
    puntos.replaceChildren(...actual.pasos.map((_, i) => {
      const p = document.createElement("span");
      if (i === indice) p.className = "activo";
      else if (i < indice) p.className = "hecho";
      return p;
    }));
    globo.querySelector("[data-rc='anterior']").disabled = indice === 0;
    const sig = globo.querySelector("[data-rc='siguiente']");
    sig.innerHTML = indice === total - 1 ? 'Terminar <i class="fas fa-check"></i>' : 'Siguiente <i class="fas fa-arrow-right"></i>';

    // Animación del globo en cada paso.
    globo.classList.remove("rc-entra");
    void globo.offsetWidth;
    globo.classList.add("rc-entra", direccion < 0 ? "rc-atras" : "rc-adelante");
    globo.classList.remove(direccion < 0 ? "rc-adelante" : "rc-atras");

    if (paso.el) {
      const r = paso.el.getBoundingClientRect();
      const fuera = r.top < 70 || r.bottom > window.innerHeight - 20;
      if (fuera) paso.el.scrollIntoView({ block: "center", behavior: "smooth" });
    }
    colocar();
    setTimeout(colocar, 350);   // después del desplazamiento suave
    sig.focus({ preventScroll: true });
  }

  function final() {
    actual.i = actual.pasos.length;
    globo.classList.add("rc-final");
    globo.classList.remove("rc-globo-centro");
    foco.classList.add("rc-foco-centro");
    foco.style.cssText = "";
    globo.classList.add("rc-globo-centro");
    globo.style.left = globo.style.top = "";
    globo.querySelector(".rc-titulo").textContent = "¡Listo! Ya conoces " + actual.def.titulo;
    globo.querySelector(".rc-texto").textContent = "Puedes repetir este recorrido cuando quieras desde el manual.";
    globo.querySelector(".rc-paso").textContent = "";
    globo.querySelector(".rc-puntos").replaceChildren();
    const botones = globo.querySelector(".rc-botones");
    botones.innerHTML =
      '<button type="button" class="rc-btn rc-btn-sec" data-rc="manual"><i class="fas fa-book-open"></i> Volver al manual</button>' +
      '<button type="button" class="rc-btn" data-rc="terminar">Terminar <i class="fas fa-check"></i></button>';
    globo.classList.remove("rc-entra");
    void globo.offsetWidth;
    globo.classList.add("rc-entra");
    botones.querySelector("[data-rc='terminar']").focus({ preventScroll: true });
  }

  function terminar() {
    if (!capa) return;
    actual = null;
    document.removeEventListener("keydown", teclas, true);
    window.removeEventListener("scroll", seguir, true);
    window.removeEventListener("resize", seguir);
    capa.classList.add("rc-saliendo");
    const vieja = capa;
    setTimeout(() => vieja.remove(), 250);
    capa = foco = globo = null;
    document.documentElement.classList.remove("rc-activo");
  }

  function iniciar(id) {
    const def = RECORRIDOS[id];
    if (!def) return false;
    if (capa) terminar();

    // Solo los pasos cuyo elemento está en esta pantalla (los de bienvenida, sin "donde", siempre).
    const pasos = def.pasos
      .map((p) => Object.assign({}, p, { el: buscarElemento(p.donde) }))
      .filter((p) => !p.donde || p.el);
    if (!pasos.length) return false;

    actual = { id, def, pasos, i: 0 };
    crearCapa();
    document.documentElement.classList.add("rc-activo");
    document.addEventListener("keydown", teclas, true);
    window.addEventListener("scroll", seguir, true);
    window.addEventListener("resize", seguir);
    ir(0, 1);
    return true;
  }

  window.PremiumRecorrido = { iniciar, terminar, recorridos: RECORRIDOS };

  // ?recorrido=<id> en la dirección: viene del botón "Muéstrame en vivo".
  const parametros = new URLSearchParams(window.location.search);
  const pedido = parametros.get("recorrido");
  if (pedido) {
    parametros.delete("recorrido");
    const limpia = window.location.pathname + (parametros.toString() ? "?" + parametros : "") + window.location.hash;
    window.history.replaceState(null, "", limpia);
    // Espera a que la pantalla termine de pintarse (y sus animaciones de entrada).
    window.addEventListener("load", () => setTimeout(() => iniciar(pedido), 450));
  }
})();
