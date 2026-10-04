// ═══════════════════════════════════════════════════════════════════════
// Burbuja flotante de contacto — Premium Eventos JM
//
// Controla 3 piezas:
//   1) El botón circular "JM" (abre/cierra el panel de opciones)
//   2) El panel de opciones (WhatsApp / Chatbot)
//   3) La ventana del chatbot (envía cada mensaje a /chatbot/mensaje/;
//      Django arma el contexto y n8n responde con IA, ver
//      Bd_PremiumEventos/chatbot.py)
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
  const chatSugerencias = document.getElementById("jmChatSugerencias");
  const chatReiniciar = document.getElementById("jmChatReiniciar");
  const chatSaludo = document.getElementById("jmChatSaludo");
  const chatEnviar = chatForm ? chatForm.querySelector("button[type=submit]") : null;
  const WHATSAPP = "https://wa.me/573117758162";

  // Escapa el texto y convierte en enlaces las URLs que mande el bot.
  // (Nunca se usa innerHTML con el texto crudo: la respuesta viene de una IA.)
  function textoConEnlaces(texto) {
    const div = document.createElement("div");
    div.textContent = texto;
    return div.innerHTML.replace(
      /(https?:\/\/[^\s<]+[^\s<.,;:!?)])/g,
      '<a href="$1" target="_blank" rel="noopener">$1</a>'
    );
  }

  function agregarMensaje(texto, autor) {
    if (!chatBody) return null;
    const burbuja = document.createElement("div");
    burbuja.className = "jm-chat-msg " + (autor === "user" ? "jm-chat-msg-user" : "jm-chat-msg-bot");
    if (autor === "user") {
      burbuja.textContent = texto;
    } else {
      burbuja.innerHTML = textoConEnlaces(texto);
    }
    chatBody.appendChild(burbuja);
    chatBody.scrollTop = chatBody.scrollHeight;
    return burbuja;
  }

  function mostrarEscribiendo() {
    const burbuja = document.createElement("div");
    burbuja.className = "jm-chat-msg jm-chat-msg-bot";
    burbuja.innerHTML = '<span class="jm-chat-typing" aria-label="Escribiendo"><span></span><span></span><span></span></span>';
    chatBody.appendChild(burbuja);
    chatBody.scrollTop = chatBody.scrollHeight;
    return burbuja;
  }

  function bloquearEnvio(bloquear) {
    if (chatInput) chatInput.disabled = bloquear;
    if (chatEnviar) chatEnviar.disabled = bloquear;
  }

  function tokenCsrf() {
    const campo = chatForm ? chatForm.querySelector("input[name=csrfmiddlewaretoken]") : null;
    return campo ? campo.value : "";
  }

  async function obtenerRespuestaBot(mensajeUsuario) {
    const respuesta = await fetch(chatForm.dataset.url, {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-CSRFToken": tokenCsrf() },
      body: JSON.stringify({ mensaje: mensajeUsuario }),
    });
    const datos = await respuesta.json().catch(() => ({}));
    return datos.respuesta || datos.error ||
      "No pude responder en este momento. Escríbenos por WhatsApp: " + WHATSAPP;
  }

  async function enviarMensaje(mensaje) {
    mensaje = mensaje.trim();
    if (!mensaje || (chatInput && chatInput.disabled)) return;

    if (chatSugerencias) chatSugerencias.remove();
    agregarMensaje(mensaje, "user");
    if (chatInput) chatInput.value = "";
    bloquearEnvio(true);
    const escribiendo = mostrarEscribiendo();

    let respuesta;
    try {
      respuesta = await obtenerRespuestaBot(mensaje);
    } catch (error) {
      respuesta = "Parece que hay un problema de conexión. Intenta de nuevo o escríbenos por WhatsApp: " + WHATSAPP;
    }
    escribiendo.remove();
    agregarMensaje(respuesta, "bot");
    bloquearEnvio(false);
    if (chatInput) chatInput.focus();
  }

  function manejarEnvioChat(event) {
    event.preventDefault();
    if (chatInput) enviarMensaje(chatInput.value);
  }

  if (chatSugerencias) {
    chatSugerencias.querySelectorAll("button").forEach((boton) => {
      boton.addEventListener("click", () => enviarMensaje(boton.textContent));
    });
  }

  // "Nueva conversación": borra el historial en el servidor y en pantalla
  if (chatReiniciar && chatForm) {
    chatReiniciar.addEventListener("click", async () => {
      try {
        await fetch(chatForm.dataset.urlReiniciar, {
          method: "POST",
          headers: { "X-CSRFToken": tokenCsrf() },
        });
      } catch (error) { /* si falla, igual se limpia la pantalla */ }
      chatBody.querySelectorAll(".jm-chat-msg").forEach((msg) => {
        if (msg !== chatSaludo) msg.remove();
      });
      if (chatInput) chatInput.focus();
    });
  }

  if (chatForm) {
    chatForm.addEventListener("submit", manejarEnvioChat);
  }
});
