
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
    // invitados. Basado en la tabla de paquetes de Premium Eventos JM.
    //
    //   Invitados | Precio del paquete | Precio por invitado (referencia)
    //   20        | $1.800.000         | $90.000
    //   30        | $2.600.000         | $86.000
    //   40        | $3.200.000         | $80.000
    //   50        | $3.900.000         | $78.000
    //   60        | $4.500.000         | $75.000
    //   70        | $4.900.000         | $70.000
    //   80        | $5.440.000         | $68.000
    //   90        | $5.850.000         | $65.000
    //   100       | $5.800.000         | $58.000
    //
    // Reglas de cálculo:
    //   - Para una cantidad de invitados que coincide con un tramo de la
    //     tabla, se usa directamente el precio de ese paquete.
    //   - Para una cantidad entre dos tramos, se interpola linealmente
    //     entre el paquete inferior y el superior.
    //   - Para menos de 20 invitados, se cobra el paquete mínimo (20).
    //   - Para más de 100 invitados, se toma el paquete de 100 como base
    //     y se suma el valor por invitado adicional ($58.000 c/u, la
    //     tarifa vigente en el último tramo).
    // ─────────────────────────────────────────────────────────────────────
    const TABLA_PAQUETES = [
      { invitados: 20, precio: 1800000 },
      { invitados: 30, precio: 2600000 },
      { invitados: 40, precio: 3200000 },
      { invitados: 50, precio: 3900000 },
      { invitados: 60, precio: 4500000 },
      { invitados: 70, precio: 4900000 },
      { invitados: 80, precio: 5440000 },
      { invitados: 90, precio: 5850000 },
      { invitados: 100, precio: 5800000 },
    ];
    const TARIFA_INVITADO_ADICIONAL = 58000; // usada para eventos de más de 100 personas

    function calcularPrecioEstimado(cantidadInvitados) {
      const n = Number(cantidadInvitados);
      if (!n || n <= 0) return null;

      const primero = TABLA_PAQUETES[0];
      const ultimo = TABLA_PAQUETES[TABLA_PAQUETES.length - 1];

      // Menos del mínimo: se cobra el paquete base de 20 invitados
      if (n <= primero.invitados) {
        return primero.precio;
      }

      // Más del máximo de la tabla: paquete de 100 + tarifa por invitado extra
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
