// ═══════════════════════════════════════════════════════════════════════
// Burbuja flotante de contacto — Premium Eventos JM
//
// Controla 3 piezas:
//   1) El botón circular "JM" (abre/cierra el panel de opciones)
//   2) El panel de opciones (WhatsApp / Chatbot)
//   3) La ventana del chatbot (placeholder, lista para conectarse a n8n)
// ═══════════════════════════════════════════════════════════════════════

document.addEventListener("DOMContentLoaded", () => {
  const widget = document.getElementById("jmWidget");
  const toggleBtn = document.getElementById("jmWidgetToggle");
  const panel = document.getElementById("jmWidgetPanel");

  const chatBtn = document.getElementById("jmChatbotBtn");
  const chatWindow = document.getElementById("jmChatWindow");
  const chatClose = document.getElementById("jmChatClose");
  const chatForm = document.getElementById("jmChatForm");
  const chatInput = document.getElementById("jmChatInput");
  const chatBody = document.getElementById("jmChatBody");

  if (!widget || !toggleBtn || !panel) return;

  // ── Abrir / cerrar el panel principal ────────────────────────────
  function abrirPanel() {
    widget.classList.add("is-open");
    toggleBtn.setAttribute("aria-expanded", "true");
  }

  function cerrarPanel() {
    widget.classList.remove("is-open");
    toggleBtn.setAttribute("aria-expanded", "false");
    cerrarChat(); // si el chat estaba abierto, se cierra también
  }

  toggleBtn.addEventListener("click", () => {
    const abierto = widget.classList.contains("is-open");
    if (abierto) {
      cerrarPanel();
    } else {
      abrirPanel();
    }
  });

  // Cierra el panel si el usuario hace clic afuera de la burbuja
  document.addEventListener("click", (event) => {
    if (!widget.contains(event.target)) {
      cerrarPanel();
    }
  });

  // ── Ventana del chatbot ───────────────────────────────────────────
  function abrirChat() {
    if (!chatWindow) return;
    chatWindow.classList.add("is-open");
    panel.style.display = "none"; // se oculta el panel de opciones mientras se chatea
    if (chatInput) chatInput.focus();
  }

  function cerrarChat() {
    if (!chatWindow) return;
    chatWindow.classList.remove("is-open");
    panel.style.display = ""; // vuelve a mostrarse el panel de opciones
  }

  if (chatBtn) {
    chatBtn.addEventListener("click", abrirChat);
  }
  if (chatClose) {
    chatClose.addEventListener("click", () => {
      cerrarChat();
    });
  }

  // No cerrar el panel/chat si se hace clic dentro de la ventana de chat
  if (chatWindow) {
    chatWindow.addEventListener("click", (event) => event.stopPropagation());
  }

  // ── Envío de mensajes en el chat ──────────────────────────────────
  function agregarMensaje(texto, autor) {
    if (!chatBody) return;
    const burbuja = document.createElement("div");
    burbuja.className = "jm-chat-msg " + (autor === "user" ? "jm-chat-msg-user" : "jm-chat-msg-bot");
    burbuja.textContent = texto;
    chatBody.appendChild(burbuja);
    chatBody.scrollTop = chatBody.scrollHeight;
  }

  // ─────────────────────────────────────────────────────────────────
  // PUNTO DE INTEGRACIÓN CON N8N
  //
  // Por ahora esta función solo simula una respuesta ("placeholder"),
  // para que el botón de chat ya se sienta funcional mientras se
  // conecta el flujo real en n8n.
  //
  // Cuando el webhook de n8n esté listo, reemplaza el contenido de
  // esta función por algo como:
  //
  //   async function obtenerRespuestaBot(mensajeUsuario) {
  //     const respuesta = await fetch("https://TU-INSTANCIA-N8N/webhook/chatbot-jm", {
  //       method: "POST",
  //       headers: { "Content-Type": "application/json" },
  //       body: JSON.stringify({ mensaje: mensajeUsuario }),
  //     });
  //     const datos = await respuesta.json();
  //     return datos.respuesta; // o el campo que devuelva tu flujo de n8n
  //   }
  //
  // Y en manejarEnvioChat() cambia la llamada a:
  //   const respuesta = await obtenerRespuestaBot(mensaje);
  //   agregarMensaje(respuesta, "bot");
  // ─────────────────────────────────────────────────────────────────
  function obtenerRespuestaBotPlaceholder(mensajeUsuario) {
    return "¡Gracias por escribirnos! Este asistente todavía está en construcción. " +
           "Muy pronto podré responderte automáticamente. Mientras tanto, un asesor " +
           "te contestará por WhatsApp con gusto.";
  }

  function manejarEnvioChat(event) {
    event.preventDefault();
    if (!chatInput) return;

    const mensaje = chatInput.value.trim();
    if (!mensaje) return;

    agregarMensaje(mensaje, "user");
    chatInput.value = "";

    // Simula que el asistente está "escribiendo" antes de responder.
    // (Cuando se conecte n8n, este setTimeout se reemplaza por el
    // await a obtenerRespuestaBot() descrito arriba.)
    setTimeout(() => {
      const respuesta = obtenerRespuestaBotPlaceholder(mensaje);
      agregarMensaje(respuesta, "bot");
    }, 700);
  }

  if (chatForm) {
    chatForm.addEventListener("submit", manejarEnvioChat);
  }
});
