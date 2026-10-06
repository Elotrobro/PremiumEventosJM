// ═══════════════════════════════════════════════════════════════════════
// Contraseña segura — lista de requisitos que se marca mientras se escribe.
//
// Se activa en cualquier <input> con el atributo data-contrasena-fuerte
// (registro en base.html y nueva contraseña en la recuperación). Son las
// mismas reglas de Bd_PremiumEventos/validaciones.py; el servidor las
// vuelve a revisar siempre, esto solo ayuda a escribirla bien a la primera.
// ═══════════════════════════════════════════════════════════════════════

document.addEventListener("DOMContentLoaded", () => {
  const REGLAS = [
    { texto: "Mínimo 8 caracteres", cumple: (v) => v.length >= 8 },
    { texto: "Al menos un número", cumple: (v) => /\d/.test(v) },
    { texto: "Al menos una letra mayúscula", cumple: (v) => v !== v.toLowerCase() },
  ];

  document.querySelectorAll("input[data-contrasena-fuerte]").forEach((input) => {
    const lista = document.createElement("ul");
    lista.className = "contrasena-reglas";
    const items = REGLAS.map((regla) => {
      const li = document.createElement("li");
      li.textContent = regla.texto;
      lista.appendChild(li);
      return li;
    });

    // La lista va debajo del campo (o del contenedor con el botón del "ojito").
    const ancla = input.closest(".password-input-wrapper") || input;
    ancla.insertAdjacentElement("afterend", lista);

    const revisar = () => {
      const valor = input.value;
      let faltantes = [];
      REGLAS.forEach((regla, i) => {
        const ok = regla.cumple(valor);
        items[i].classList.toggle("cumple", ok);
        if (!ok) faltantes.push(regla.texto.toLowerCase());
      });
      // Bloquea el envío del formulario con un mensaje claro si falta algo.
      input.setCustomValidity(
        valor && faltantes.length ? "La contraseña necesita: " + faltantes.join(", ") + "." : ""
      );
    };

    input.addEventListener("input", revisar);
    revisar();
  });
});
