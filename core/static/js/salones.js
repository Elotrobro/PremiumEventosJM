// ============================================================
// Salones y espacios (convenios.html): ventana de detalle
//
// Al hacer clic en una tarjeta (o en el nombre del salón, que es un
// botón para poder usarlo con el teclado) se abre #modalSalon con la
// información completa y las fotos de ese salón. El contenido de cada
// salón ya viene escrito por Django en <template id="salonDetalle-N">;
// aquí solo se copia a la ventana y se maneja el visor de fotos.
// La animación de zoom está en css/convenios.css.
// ============================================================

(function () {
  const modal = document.getElementById("modalSalon");
  const cuerpo = document.getElementById("modalSalonCuerpo");
  const titulo = document.getElementById("modalSalonTitulo");
  if (!modal || !cuerpo || !titulo) return;

  let fotos = [];
  let miniaturas = [];
  let indice = 0;

  function mostrarFoto(nuevo) {
    if (!fotos.length) return;
    indice = (nuevo + fotos.length) % fotos.length; // da la vuelta al llegar al final
    fotos.forEach((foto, i) => foto.classList.toggle("activa", i === indice));
    miniaturas.forEach((mini, i) => {
      mini.classList.toggle("activa", i === indice);
      mini.setAttribute("aria-current", i === indice ? "true" : "false");
    });
    const actual = cuerpo.querySelector("[data-actual]");
    if (actual) actual.textContent = String(indice + 1);
    const activa = miniaturas[indice];
    if (activa) activa.scrollIntoView({ block: "nearest", inline: "nearest" });
  }

  function abrirSalon(id) {
    const plantilla = document.getElementById("salonDetalle-" + id);
    if (!plantilla) return;

    titulo.textContent = plantilla.dataset.nombre;
    cuerpo.replaceChildren(plantilla.content.cloneNode(true));
    cuerpo.scrollTop = 0;

    fotos = Array.from(cuerpo.querySelectorAll(".salon-galeria-foto"));
    miniaturas = Array.from(cuerpo.querySelectorAll(".salon-miniatura"));
    indice = 0;
    mostrarFoto(0);

    modal.showModal();
    // El foco va al contenido (no a la ×), así las flechas del teclado
    // pasan las fotos de una vez y la × no aparece remarcada al abrir.
    cuerpo.focus({ preventScroll: true });
  }

  // Abrir: clic en cualquier parte de la tarjeta, salvo el botón de cotizar.
  document.addEventListener("click", function (e) {
    if (e.target.closest(".cotizar-salon-link")) return;
    const disparador = e.target.closest(".salon-card[data-salon], .salon-ver-detalle");
    if (disparador && !modal.contains(disparador)) {
      abrirSalon(disparador.dataset.salon);
    }
  });

  // Dentro de la ventana: cerrar, flechas y miniaturas.
  modal.addEventListener("click", function (e) {
    if (e.target.closest("[data-cerrar-salon]")) {
      modal.close();
      return;
    }
    const flecha = e.target.closest(".salon-galeria-flecha");
    if (flecha) {
      mostrarFoto(indice + Number(flecha.dataset.paso));
      return;
    }
    const mini = e.target.closest(".salon-miniatura");
    if (mini) {
      mostrarFoto(Number(mini.dataset.indice));
      return;
    }
    // Clic en el fondo oscuro (fuera del recuadro): cerrar, como el modal de cotización.
    const r = modal.getBoundingClientRect();
    const fuera = e.clientX < r.left || e.clientX > r.right || e.clientY < r.top || e.clientY > r.bottom;
    if (fuera && e.target === modal) modal.close();
  });

  // Flechas del teclado para pasar las fotos (Esc ya cierra el <dialog>).
  modal.addEventListener("keydown", function (e) {
    if (fotos.length < 2) return;
    if (e.key === "ArrowLeft") { e.preventDefault(); mostrarFoto(indice - 1); }
    if (e.key === "ArrowRight") { e.preventDefault(); mostrarFoto(indice + 1); }
  });
})();
