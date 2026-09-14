// Lógica del catálogo de alquiler: filtros por categoría, carrito de
// cotización y envío del resumen por WhatsApp.
// (antes vivía como <script> inline dentro de catalogo.html)
//
// ⚠️ Este carrito vive SOLO en esta variable de JavaScript (en memoria del
// navegador): no se guarda en la base de datos ni en localStorage, así que
// se pierde por completo si el usuario recarga la página. Los modelos
// CarritoSeleccion/DetalleCarrito existen en Bd_PremiumEventos/models.py
// para persistir esto en el futuro, pero todavía no están conectados aquí.

document.addEventListener("DOMContentLoaded", function () {
        let carrito = {};  // objeto en memoria: { idProducto: { nombre, precio, cantidad } }

        // El estado de sesión viene del backend como atributo en <body>
        // (ver data-logged-in en core/templates/base.html), llenado según
        // request.session.usuario_id en cada request.
        const usuarioLogueado = document.body.dataset.loggedIn === "true";

        // ── Filtrado por categoría ──────────────────────────────────────
        // Cada botón de filtro tiene data-filtro="mobiliario|textiles|decoracion|todos"
        // y cada tarjeta de producto tiene data-categoria con el mismo valor;
        // simplemente se muestran/ocultan tarjetas comparando esos atributos.
        const botonesFiltro = document.querySelectorAll(".btn-filtro");
        botonesFiltro.forEach(boton => {
            boton.addEventListener("click", () => {
                botonesFiltro.forEach(b => b.classList.remove("active", "btn-dark"));
                botonesFiltro.forEach(b => b.classList.add("btn-outline-dark"));
                boton.classList.add("active", "btn-dark");
                boton.classList.remove("btn-outline-dark");

                const filtro = boton.getAttribute("data-filtro");
                document.querySelectorAll(".item-card-wrapper").forEach(card => {
                    if (filtro === "todos" || card.getAttribute("data-categoria") === filtro) {
                        card.style.display = "block";
                    } else {
                        card.style.display = "none";
                    }
                });
            });
        });

        // ── Agregar al carrito ───────────────────────────────────────────
        // Los datos del producto (id, nombre, precio) se leen directamente
        // de los atributos data-* de la tarjeta HTML (ver catalogo.html),
        // ya que no vienen de una API ni de la base de datos.
        document.querySelectorAll(".agregar-item").forEach(button => {
            button.addEventListener("click", (e) => {
                const wrapper = e.target.closest(".item-card-wrapper");
                const id = wrapper.getAttribute("data-id");
                const nombre = wrapper.getAttribute("data-nombre");
                const precio = parseFloat(wrapper.getAttribute("data-precio"));

                if (carrito[id]) {
                    // Ya estaba en el carrito: solo se incrementa la cantidad
                    carrito[id].cantidad += 1;
                } else {
                    // Primera vez que se agrega este producto
                    carrito[id] = { nombre, precio, cantidad: 1 };
                }
                actualizarCarrito();
            });
        });

        // Repinta por completo el panel lateral del carrito a partir del
        // objeto `carrito` en memoria: lista de ítems, contador y total.
        // Se llama después de cualquier cambio (agregar/quitar/vaciar).
        function actualizarCarrito() {
            const listaCarrito = document.getElementById("lista-carrito");
            const contadorItems = document.getElementById("contador-items");
            const totalCotizacion = document.getElementById("total-cotizacion");
            const btnEnviar = document.getElementById("btn-enviar-cotizacion");
            const btnVaciar = document.getElementById("btn-vaciar-carrito");

            listaCarrito.innerHTML = "";
            let total = 0;
            let cantidadTotal = 0;
            let keys = Object.keys(carrito);

            if (keys.length === 0) {
                listaCarrito.innerHTML = `<p class="text-muted text-center py-4 my-0" id="carrito-vacio">No has seleccionado ningún elemento todavía.</p>`;
                btnEnviar.disabled = true;
                btnVaciar.disabled = true;
                contadorItems.textContent = "0 ítems";
                totalCotizacion.textContent = "$0";
                return;
            }

            btnEnviar.disabled = false;
            btnVaciar.disabled = false;

            keys.forEach(id => {
                let item = carrito[id];
                let subtotal = item.precio * item.cantidad;
                total += subtotal;
                cantidadTotal += item.cantidad;

                let div = document.createElement("div");
                div.className = "d-flex justify-content-between align-items-center mb-2 border-bottom pb-2";
                div.innerHTML = `
                    <div>
                        <h6 class="mb-0 fs-6 fw-bold">${item.nombre}</h6>
                        <small class="text-muted">$${item.precio.toLocaleString()} c/u</small>
                    </div>
                    <div class="d-flex align-items-center gap-2">
                        <button class="btn btn-sm btn-outline-secondary px-1 py-0 decrementar" data-id="${id}">-</button>
                        <span class="fw-bold">${item.cantidad}</span>
                        <button class="btn btn-sm btn-outline-secondary px-1 py-0 incrementar" data-id="${id}">+</button>
                        <button class="btn btn-sm text-danger ms-2 eliminar" data-id="${id}"><i class="fas fa-times"></i></button>
                    </div>
                `;
                listaCarrito.appendChild(div);
            });

            contadorItems.textContent = `${cantidadTotal} ${cantidadTotal === 1 ? 'ítem' : 'ítems'}`;
            totalCotizacion.textContent = `$${total.toLocaleString()}`;

            // Eventos para botones dentro del carrito
            document.querySelectorAll(".incrementar").forEach(btn => {
                btn.addEventListener("click", (e) => {
                    carrito[e.target.getAttribute("data-id")].cantidad += 1;
                    actualizarCarrito();
                });
            });

            document.querySelectorAll(".decrementar").forEach(btn => {
                btn.addEventListener("click", (e) => {
                    let id = e.target.getAttribute("data-id");
                    if (carrito[id].cantidad > 1) {
                        carrito[id].cantidad -= 1;
                    } else {
                        delete carrito[id];
                    }
                    actualizarCarrito();
                });
            });

            document.querySelectorAll(".eliminar").forEach(btn => {
                btn.addEventListener("click", (e) => {
                    delete carrito[e.target.closest("button").getAttribute("data-id")];
                    actualizarCarrito();
                });
            });
        }

        // Vaciar carrito: simplemente se reinicia el objeto en memoria
        document.getElementById("btn-vaciar-carrito").addEventListener("click", () => {
            carrito = {};
            actualizarCarrito();
        });

        // ── Enviar por WhatsApp ──────────────────────────────────────────
        // Nota: esto NO guarda nada en la base de datos ni pasa por el
        // backend de Django; simplemente arma un mensaje de texto y abre
        // WhatsApp Web/App con ese mensaje precargado (wa.me), para que el
        // usuario lo envíe manualmente. El "%0A" es un salto de línea
        // codificado para URL (el equivalente a "\n" dentro de un enlace).
        document.getElementById("btn-enviar-cotizacion").addEventListener("click", () => {
            // Validación: no se puede enviar una cotización sin haber iniciado sesión
            // (mismo patrón de bloqueo que usa modal.js para el formulario de inicio.html).
            if (!usuarioLogueado) {
                alert("Debes iniciar sesión para poder solicitar una cotización.");
                // La modal de login vive en base.html (visible en toda página);
                // se abre directamente en vez de navegar a otra URL.
                if (window.abrirLoginModal) {
                    window.abrirLoginModal();
                } else {
                    window.location.href = "/?login=1";
                }
                return;
            }

            let mensaje = "Hola, *Premium Eventos JM*, me gustaría solicitar la siguiente cotización de alquiler:%0A%0A";
            let total = 0;
            Object.keys(carrito).forEach(id => {
                let item = carrito[id];
                let subtotal = item.precio * item.cantidad;
                total += subtotal;
                mensaje += `- ${item.cantidad}x ${item.nombre} ($${subtotal.toLocaleString()})%0A`;
            });
            mensaje += `%0A*Total Estimado: $${total.toLocaleString()}*`;
            // ⚠️ Este número de WhatsApp (573000000000) parece un placeholder
            // de prueba; conviene confirmar que sea el número real de la
            // empresa antes de publicar el sitio.
            window.open(`https://wa.me/573226513598?text=${mensaje}`, '_blank');
        });
    });
