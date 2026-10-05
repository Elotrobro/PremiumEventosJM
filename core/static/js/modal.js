
    const modalCotizacion = document.getElementById("modalCotizacion");
    const formCotizacion = document.getElementById("formCotizacion");
    const inputFechaEvento = document.getElementById("fecha_evento");
    const inputHoraEvento = document.querySelector("#hora_evento")

    // Devuelve la fecha de hoy en formato YYYY-MM-DD (zona horaria local),
    // que es el formato que exige el atributo "min" de un <input type="date">.
  // ============================================================
// VALIDACIÓN DE FECHA Y HORA DEL EVENTO
// ============================================================

// Devuelve una fecha en formato YYYY-MM-DD
// usando la fecha local del PC del usuario.
const obtenerFechaISO = (fecha) => {

  const año = fecha.getFullYear();
  const mes = String(fecha.getMonth() + 1).padStart(2, "0");
  const dia = String(fecha.getDate()).padStart(2, "0");

  return `${año}-${mes}-${dia}`;
};


// Devuelve la fecha de mañana.
const obtenerFechaMañanaISO = () => {

  const mañana = new Date();

  mañana.setDate(mañana.getDate() + 1);

  return obtenerFechaISO(mañana);
};


// Establece como fecha mínima mañana.
// Así el calendario no permite seleccionar hoy ni fechas anteriores.
function actualizarFechaMinima() {

  if (inputFechaEvento) {

    inputFechaEvento.setAttribute(
      "min",
      obtenerFechaMañanaISO()
    );

  }
}


// ============================================================
// GENERAR HORARIOS
// ============================================================

function generarHorasDisponibles() {

  if (!inputHoraEvento || !inputFechaEvento) {
    return;
  }

  const fechaSeleccionada = inputFechaEvento.value;

  // Limpiar las opciones anteriores
  inputHoraEvento.innerHTML = "";

  // Opción inicial
  const opcionInicial = document.createElement("option");

  opcionInicial.value = "";
  opcionInicial.textContent = "Seleccione una hora";
  opcionInicial.disabled = true;
  opcionInicial.selected = true;

  inputHoraEvento.appendChild(opcionInicial);


  // Si todavía no hay fecha seleccionada
  if (!fechaSeleccionada) {

    inputHoraEvento.disabled = true;

    return;
  }


  const fechaMañana = obtenerFechaMañanaISO();

  let horaInicial = 0;


  // ==========================================================
  // SI EL EVENTO ES MAÑANA
  // ==========================================================

  if (fechaSeleccionada === fechaMañana) {

    const ahora = new Date();

    /*
     * Se toma la hora del PC.
     *
     * Ejemplo:
     * 3:15 PM → primera hora = 4:00 PM
     * 3:45 PM → primera hora = 4:00 PM
     * 4:00 PM → primera hora = 5:00 PM
     */

    horaInicial = ahora.getHours() + 1;


    // Si ya son las 11 PM o más,
    // no quedan horarios disponibles para mañana.
    if (horaInicial > 23) {

      inputHoraEvento.innerHTML = "";

      const sinHorarios = document.createElement("option");

      sinHorarios.value = "";
      sinHorarios.textContent =
        "No hay horarios disponibles para mañana";

      sinHorarios.disabled = true;
      sinHorarios.selected = true;

      inputHoraEvento.appendChild(sinHorarios);

      inputHoraEvento.disabled = true;

      return;
    }

  } else {

    // ========================================================
    // SI ES PASADO MAÑANA O CUALQUIER FECHA POSTERIOR
    // ========================================================

    horaInicial = 0;
  }


  // ==========================================================
  // CREAR LAS HORAS
  // ==========================================================

  for (let hora = horaInicial; hora <= 23; hora++) {

    let hora12;
    let periodo;


    if (hora === 0) {

      hora12 = 12;
      periodo = "AM";

    } else if (hora < 12) {

      hora12 = hora;
      periodo = "AM";

    } else if (hora === 12) {

      hora12 = 12;
      periodo = "PM";

    } else {

      hora12 = hora - 12;
      periodo = "PM";
    }


    const hora24 = String(hora).padStart(2, "0") + ":00";


    const opcion = document.createElement("option");

    // Lo que recibirá Django
    opcion.value = hora24;

    // Lo que verá el usuario
    opcion.textContent = `${hora12}:00 ${periodo}`;

    inputHoraEvento.appendChild(opcion);
  }


  inputHoraEvento.disabled = false;
}


// ============================================================
// INICIALIZAR
// ============================================================

actualizarFechaMinima();

if (inputHoraEvento) {
  inputHoraEvento.disabled = true;
}


// ============================================================
// CUANDO EL USUARIO CAMBIA LA FECHA
// ============================================================

if (inputFechaEvento) {

  inputFechaEvento.addEventListener("change", () => {

    generarHorasDisponibles();

  });

}

    function abrirModalCotizacion() {
      actualizarFechaMinima();
      modalCotizacion.showModal();
    }

    function cerrarModalCotizacion() {
      modalCotizacion.close();
    }

    modalCotizacion.addEventListener("click", function (event) {
      const rect = modalCotizacion.getBoundingClientRect();
      const dentro =
        event.clientX >= rect.left &&
        event.clientX <= rect.right &&
        event.clientY >= rect.top &&
        event.clientY <= rect.bottom;

      if (!dentro) {
        modalCotizacion.close();
      }
    });

    // Validación de sesión: solo un usuario autenticado puede enviar una
    // solicitud de cotización. El estado de la sesión viene del backend
    // como atributo data-logged-in en <body> (ver base.html).
    if (formCotizacion) {
      formCotizacion.addEventListener("submit", function (event) {
        const usuarioAutenticado = document.body.dataset.loggedIn === "true";

        if (!usuarioAutenticado) {
          event.preventDefault();
          modalCotizacion.close();
          alert("Debes iniciar sesión para realizar una cotización.");
          // La modal de login vive en base.html (visible en toda página);
          // se abre directamente en vez de navegar a otra URL.
          if (window.abrirLoginModal) {
            window.abrirLoginModal();
          } else {
            window.location.href = "/?login=1";
          }
          return;
        }

        // Segunda barrera de validación para la fecha del evento: aunque el
        // atributo "min" ya deshabilita (en gris) los días pasados en el
        // calendario nativo, se vuelve a comprobar aquí por si el valor
        // llegó manipulado (autocompletado, DevTools, etc.).
        if (inputFechaEvento && inputFechaEvento.value) {
          const fechaSeleccionada = inputFechaEvento.value; // formato YYYY-MM-DD
          if (fechaSeleccionada < obtenerFechaHoyISO()) {
            event.preventDefault();
            alert("La fecha del evento no puede ser una fecha que ya pasó. Por favor selecciona una fecha válida.");
            inputFechaEvento.focus();
            return;
          }
        }

        // Muestra el cálculo del posible costo del evento justo en el
        // momento de realizar la cotización, según la cantidad de
        // invitados ingresada.
        const invitadosInput = document.getElementById("invitados");
        const precio = invitadosInput ? calcularPrecioEstimado(invitadosInput.value) : null;

        if (precio !== null) {
          alert(
            "Costo estimado para tu evento: " + formatearCOP(precio) + "\n\n" +
            "Atención, esta es una cotización aproximada de lo que puede costar el evento."
          );
        }
      });
    }

    // ─────────────────────────────────────────────────────────────────────
    // Lógica de negocio: cálculo del precio estimado según cantidad de
    // invitados. La tabla NO está escrita aquí: la edita la administradora
    // en el panel (Precios) y llega en el <script id="tabla-precios"> que
    // pone inicio.html. Es el mismo cálculo de Bd_PremiumEventos/precios.py:
    //   - Si coincide con un tramo, se usa el precio de ese tramo.
    //   - Entre dos tramos se interpola en línea recta (redondeo a miles).
    //   - Por debajo del primer tramo se cobra el primer tramo.
    //   - Por encima del último tramo se suma la tarifa por invitado adicional.
    // ─────────────────────────────────────────────────────────────────────
    const elementoTablaPrecios = document.getElementById("tabla-precios");
    const DATOS_PRECIOS = elementoTablaPrecios ? JSON.parse(elementoTablaPrecios.textContent) : null;
    const TABLA_PAQUETES = DATOS_PRECIOS ? DATOS_PRECIOS.paquetes : [];
    const TARIFA_INVITADO_ADICIONAL = DATOS_PRECIOS ? DATOS_PRECIOS.tarifa_adicional : 0;

    function calcularPrecioEstimado(cantidadInvitados) {
      const n = Number(cantidadInvitados);
      if (!n || n <= 0 || !TABLA_PAQUETES.length) return null;

      const primero = TABLA_PAQUETES[0];
      const ultimo = TABLA_PAQUETES[TABLA_PAQUETES.length - 1];

      // Menos del primer tramo: se cobra el paquete mínimo
      if (n <= primero.invitados) {
        return primero.precio;
      }

      // Más del último tramo: precio de ese tramo + tarifa por invitado extra
      if (n >= ultimo.invitados) {
        const extra = n - ultimo.invitados;
        return ultimo.precio + extra * TARIFA_INVITADO_ADICIONAL;
      }

      // Entre dos tramos: interpolación lineal
      for (let i = 0; i < TABLA_PAQUETES.length - 1; i++) {
        const inferior = TABLA_PAQUETES[i];
        const superior = TABLA_PAQUETES[i + 1];

        if (n > inferior.invitados && n <= superior.invitados) {
          const proporcion = (n - inferior.invitados) / (superior.invitados - inferior.invitados);
          const precio = inferior.precio + proporcion * (superior.precio - inferior.precio);
          return Math.round(precio / 1000) * 1000; // redondeo a miles
        }
      }

      return null;
    }

    function formatearCOP(valor) {
      return "$" + Math.round(valor).toLocaleString("es-CO");
    }

    const inputInvitados = document.getElementById("invitados");
    const cajaEstimado = document.getElementById("cotizacionEstimada");
    const textoEstimado = document.getElementById("precioEstimadoTexto");
    const inputPrecioEstimado = document.getElementById("precio_estimado_input");

    function actualizarEstimado() {
      if (!inputInvitados || !cajaEstimado || !textoEstimado || !inputPrecioEstimado) return;

      const precio = calcularPrecioEstimado(inputInvitados.value);

      if (precio === null) {
        cajaEstimado.classList.add("d-none");
        inputPrecioEstimado.value = "0";
        return;
      }

      textoEstimado.textContent = formatearCOP(precio);
      inputPrecioEstimado.value = String(Math.round(precio));
      cajaEstimado.classList.remove("d-none");
    }

    if (inputInvitados) {
      inputInvitados.addEventListener("input", actualizarEstimado);
    }

    // ============================================================
// RESUMEN EN TIEMPO REAL DE LA COTIZACIÓN
// ============================================================

function actualizarResumenModal() {

    const resumen = document.getElementById("resumen-modal-cotizacion");
    const contador = document.getElementById("contador-modal-items");
    const total = document.getElementById("total-modal-cotizacion");

    if (!resumen || !contador || !total) return;

    let items = [];

    // ------------------------------------------------------------
    // Tipo de evento
    // ------------------------------------------------------------

    const tipoEvento = document.getElementById("tipo_evento");

    if (tipoEvento && tipoEvento.value) {

        const texto =
            tipoEvento.options[tipoEvento.selectedIndex].text;

        items.push({
            label: "Tipo de evento",
            valor: texto
        });
    }


    // ------------------------------------------------------------
    // Fecha
    // ------------------------------------------------------------

    const fecha = document.getElementById("fecha_evento");

    if (fecha && fecha.value) {

        let fechaTexto = fecha.value;

        const partes = fechaTexto.split("-");

        if (partes.length === 3) {
            fechaTexto =
                `${partes[2]}/${partes[1]}/${partes[0]}`;
        }

        items.push({
            label: "Fecha",
            valor: fechaTexto
        });
    }


    // ------------------------------------------------------------
    // Hora
    // ------------------------------------------------------------

    const hora = document.getElementById("hora_evento");

    if (hora && hora.value) {

        const texto =
            hora.options[hora.selectedIndex].text;

        items.push({
            label: "Hora",
            valor: texto
        });
    }


    // ------------------------------------------------------------
    // Invitados
    // ------------------------------------------------------------

    const invitados =
        document.getElementById("invitados");

    if (invitados && invitados.value) {

        items.push({
            label: "Invitados",
            valor: `${invitados.value} personas`
        });
    }


    // ------------------------------------------------------------
    // Lugar
    // ------------------------------------------------------------

    const lugar =
        document.getElementById("lugar_evento");

    if (lugar && lugar.value.trim()) {

        items.push({
            label: "Lugar",
            valor: lugar.value.trim()
        });
    }


    // ------------------------------------------------------------
    // Salón
    // ------------------------------------------------------------

    const salon =
        document.getElementById("salon");

    if (salon && salon.value) {

        const texto =
            salon.options[salon.selectedIndex].text;

        items.push({
            label: "¿Cuenta con salón?",
            valor: texto
        });
    }


    // ------------------------------------------------------------
    // Sugerencias de sede
    // ------------------------------------------------------------

    const sugerencias =
        document.getElementById("sugerencias_sede");

    if (sugerencias && sugerencias.value) {

        const texto =
            sugerencias.options[sugerencias.selectedIndex].text;

        items.push({
            label: "Sugerencias de sede",
            valor: texto
        });
    }


    // ------------------------------------------------------------
    // Servicios seleccionados
    // ------------------------------------------------------------

    const serviciosSeleccionados =
        document.querySelectorAll(
            'input[name="servicios"]:checked'
        );

    if (serviciosSeleccionados.length > 0) {

        let serviciosHTML = "";

        serviciosSeleccionados.forEach(servicio => {

            const label =
                document.querySelector(
                    `label[for="${servicio.id}"]`
                );

            const nombre =
                label
                    ? label.textContent.trim()
                    : servicio.value;

            serviciosHTML += `
                <div class="resumen-servicio-modal">
                    <i class="fas fa-check-circle"></i>
                    <span>${nombre}</span>
                </div>
            `;
        });

        items.push({
            label: "Servicios seleccionados",
            valor: serviciosHTML,
            html: true
        });
    }


    // ------------------------------------------------------------
    // Presupuesto
    // ------------------------------------------------------------

    const presupuesto =
        document.getElementById("presupuesto");

    if (presupuesto && presupuesto.value) {

        items.push({
            label: "Presupuesto aproximado",
            valor: formatearCOP(
                Number(presupuesto.value)
            )
        });
    }


    // ------------------------------------------------------------
    // Tema
    // ------------------------------------------------------------

    const tema =
        document.getElementById("tema_evento");

    if (tema && tema.value.trim()) {

        items.push({
            label: "Tema / estilo",
            valor: tema.value.trim()
        });
    }


    // ------------------------------------------------------------
    // Mostrar mensaje cuando todavía no hay información
    // ------------------------------------------------------------

    if (items.length === 0) {

        resumen.innerHTML = `
            <p class="text-muted text-center py-4 my-0">
                Completa los datos para ver el resumen.
            </p>
        `;

        contador.textContent = "0 ítems";
        total.textContent = "$0";

        return;
    }


    // ------------------------------------------------------------
    // Construir HTML
    // ------------------------------------------------------------

    resumen.innerHTML = "";

    items.forEach(item => {

        const div =
            document.createElement("div");

        div.className =
            "resumen-item-modal";

        if (item.html) {

            div.innerHTML = `
                <div class="resumen-label">
                    ${item.label}
                </div>

                <div class="resumen-valor">
                    ${item.valor}
                </div>
            `;

        } else {

            div.innerHTML = `
                <div class="resumen-label">
                    ${item.label}
                </div>

                <div class="resumen-valor">
                    ${item.valor}
                </div>
            `;
        }

        resumen.appendChild(div);
    });


    // ------------------------------------------------------------
    // Contador
    // ------------------------------------------------------------

    contador.textContent =
        `${items.length} ${items.length === 1 ? "ítem" : "ítems"}`;


    // ------------------------------------------------------------
    // Precio estimado
    // ------------------------------------------------------------

    const inputInvitados =
        document.getElementById("invitados");

    if (inputInvitados && inputInvitados.value) {

        const precio =
            calcularPrecioEstimado(
                inputInvitados.value
            );

        if (precio !== null) {

            total.textContent =
                formatearCOP(precio);

        } else {

            total.textContent = "$0";
        }

    } else {

        total.textContent = "$0";
    }
} 

// ============================================================
// ACTUALIZAR RESUMEN AL CAMBIAR CUALQUIER CAMPO
// ============================================================

const camposResumen = document.querySelectorAll(
    "#formCotizacion input, " +
    "#formCotizacion select, " +
    "#formCotizacion textarea"
);

camposResumen.forEach(campo => {

    campo.addEventListener("input", actualizarResumenModal);

    campo.addEventListener("change", actualizarResumenModal);

});

document.addEventListener("DOMContentLoaded", function () {
    const params = new URLSearchParams(window.location.search);

    if (params.get("cotizar") === "1") {
        abrirModalCotizacion();
    }
});

// ------------------------------------------------------------
// Validación: salón y sugerencias de sede
// ------------------------------------------------------------

const salonSelect = document.getElementById("salon");
const sugerenciasSedeSelect = document.getElementById("sugerencias_sede");
const sedeSugerida = document.getElementById("sede_sugerida");

if (salonSelect && sugerenciasSedeSelect) {

    function actualizarSugerenciaSede() {

        if (salonSelect.value === "si") {

            // Si ya tiene salón, no necesita sugerencias
            sugerenciasSedeSelect.value = "";
            sugerenciasSedeSelect.disabled = true;

            if (sedeSugerida) {
                sedeSugerida.classList.add("d-none");
            }

        } else if (salonSelect.value === "no") {

            // Si no tiene salón, se sugiere nuestra sede
            sugerenciasSedeSelect.disabled = false;
            sugerenciasSedeSelect.value = "si";

            if (sedeSugerida) {
                sedeSugerida.classList.remove("d-none");
            }

        } else {

            // Estado inicial
            sugerenciasSedeSelect.disabled = false;
            sugerenciasSedeSelect.value = "";

            if (sedeSugerida) {
                sedeSugerida.classList.add("d-none");
            }
        }
    }

    salonSelect.addEventListener("change", actualizarSugerenciaSede);

    // Ejecutar al cargar por si ya existe un valor seleccionado
    actualizarSugerenciaSede();
}

    // ============================================================
    // VALIDACIÓN GLOBAL DE CORREOS ELECTRÓNICOS
    // ============================================================

    const camposCorreo = document.querySelectorAll('input[type="email"]');

    camposCorreo.forEach((campo) => {

        campo.addEventListener('input', function () {

            const correo = this.value.trim();

            // Campo vacío: estado neutral
            if (correo === "") {
                this.classList.remove("correo-valido", "correo-invalido");
                this.setCustomValidity("");
                return;
            }

            /*
             * Valida:
             * usuario@dominio.extension
             *
             * Ejemplos válidos:
             * usuario@gmail.com
             * usuario@hotmail.com
             * usuario@yahoo.com
             * usuario@outlook.com
             * usuario@icloud.com
             * usuario@empresa.com.co
             *
             * No se limita a un proveedor específico.
             */
            const formatoCorreo =
                /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/;

            if (formatoCorreo.test(correo)) {

                // CORREO VÁLIDO
                this.classList.remove("correo-invalido");
                this.classList.add("correo-valido");

                this.setCustomValidity("");

            } else {

                // CORREO INVÁLIDO
                this.classList.remove("correo-valido");
                this.classList.add("correo-invalido");

                this.setCustomValidity(
                    "Ingresa un correo electrónico válido. Ejemplo: usuario@gmail.com"
                );
            }
        });

        // Validar también cuando el usuario sale del campo
        campo.addEventListener('blur', function () {

            const correo = this.value.trim();

            if (correo === "") {
                this.classList.remove("correo-valido", "correo-invalido");
                return;
            }

            const formatoCorreo =
                /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/;

            if (formatoCorreo.test(correo)) {
                this.classList.remove("correo-invalido");
                this.classList.add("correo-valido");
            } else {
                this.classList.remove("correo-valido");
                this.classList.add("correo-invalido");
            }
        });
    });

/* =========================================================
   CARRUSEL PREMIUM
   ========================================================= */

document.addEventListener("DOMContentLoaded", function () {

    const carousel = document.querySelector(".premium-carousel");

    if (!carousel) return;

    const slides = carousel.querySelectorAll(".premium-slide");
    const indicators = carousel.querySelectorAll(".premium-indicator");

    const prevButton = carousel.querySelector(".premium-prev");
    const nextButton = carousel.querySelector(".premium-next");

    let currentSlide = 0;
    let autoplay;


    function mostrarSlide(index) {

        if (index >= slides.length) {
            index = 0;
        }

        if (index < 0) {
            index = slides.length - 1;
        }

        slides.forEach(slide => {
            slide.classList.remove("active");
        });

        indicators.forEach(indicator => {
            indicator.classList.remove("active");
        });

        slides[index].classList.add("active");
        indicators[index].classList.add("active");

        currentSlide = index;
    }


    function siguiente() {
        mostrarSlide(currentSlide + 1);
    }


    function anterior() {
        mostrarSlide(currentSlide - 1);
    }


    nextButton.addEventListener("click", function () {
        siguiente();
        reiniciarAutoplay();
    });


    prevButton.addEventListener("click", function () {
        anterior();
        reiniciarAutoplay();
    });


    indicators.forEach((indicator, index) => {

        indicator.addEventListener("click", function () {

            mostrarSlide(index);

            reiniciarAutoplay();

        });

    });


    function iniciarAutoplay() {

        autoplay = setInterval(function () {

            siguiente();

        }, 5000);

    }


    function reiniciarAutoplay() {

        clearInterval(autoplay);

        iniciarAutoplay();

    }


    carousel.addEventListener("mouseenter", function () {

        clearInterval(autoplay);

    });


    carousel.addEventListener("mouseleave", function () {

        iniciarAutoplay();

    });


    /* Teclado */

    document.addEventListener("keydown", function (event) {

        if (event.key === "ArrowLeft") {

            anterior();
            reiniciarAutoplay();

        }

        if (event.key === "ArrowRight") {

            siguiente();
            reiniciarAutoplay();

        }

    });


    /* Iniciar */

    mostrarSlide(0);
    iniciarAutoplay();

});