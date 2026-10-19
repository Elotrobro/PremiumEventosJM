
(function () {
    function iniciarTestimonios() {
        const lista = document.getElementById("listaTestimonios");
        const botonMas = document.getElementById("verMasResenas");
        const botonMenos = document.getElementById("verMenosResenas");
        const contador = document.getElementById("contadorResenas");

        if (!lista || !botonMas) {
            console.warn(
                "No se encontraron los elementos necesarios para testimonios."
            );
            return;
        }

        const reducirMovimiento = window.matchMedia(
            "(prefers-reduced-motion: reduce)"
        ).matches;

        let pagina = 2;
        let cargando = false;
        let total = Number(lista.dataset.total || 0);

        let mostradas = lista.querySelectorAll(
            ".testimonio-card"
        ).length;

        // Lee el total inicial desde el contador si no viene en el HTML.
        if (!total && contador) {
            const coincidencia = contador.textContent.match(/de\s+(\d+)/i);
            if (coincidencia) {
                total = Number(coincidencia[1]);
            }
        }

        // Animación al entrar en pantalla, similar a la galería.
        function observarTarjeta(tarjeta) {
            tarjeta.classList.add("reveal-testimonio");

            if (
                reducirMovimiento ||
                !("IntersectionObserver" in window)
            ) {
                tarjeta.classList.add("is-visible");
                return;
            }

            const observador = new IntersectionObserver(
                function (entradas, observer) {
                    entradas.forEach(function (entrada) {
                        if (entrada.isIntersecting) {
                            entrada.target.classList.add("is-visible");
                            observer.unobserve(entrada.target);
                        }
                    });
                },
                {
                    threshold: 0.08,
                    rootMargin: "0px 0px -35px 0px"
                }
            );

            observador.observe(tarjeta);
        }

        // Aplica la animación a las reseñas que ya están en el HTML.
        lista.querySelectorAll(".testimonio-card").forEach(
            observarTarjeta
        );

        function actualizarContador() {
            if (contador) {
                contador.textContent =
                    `Mostrando ${mostradas} de ${total} reseñas`;
            }
        }

        function actualizarBotones(tieneMas) {
            botonMas.hidden = !tieneMas;

            if (botonMenos) {
                botonMenos.hidden = mostradas <= 5;
            }
        }

        function crearTarjeta(item) {
            const fila = document.createElement("div");
            fila.className = "row testimonio-item";
            fila.setAttribute("data-testimonio-card", "");

            const columna = document.createElement("div");
            columna.className = "col-lg-8 mx-auto";

            const tarjeta = document.createElement("div");
            tarjeta.className = "testimonio-card";

            const estrellas = document.createElement("div");
            estrellas.className = "estrellas";
            estrellas.setAttribute("role", "img");
            estrellas.setAttribute(
                "aria-label",
                `Calificación: ${item.calificacion} de 5 estrellas`
            );

            const calificacion = Math.max(
                0,
                Math.min(5, Number(item.calificacion) || 0)
            );

            for (let i = 1; i <= 5; i++) {
                const estrella = document.createElement("i");

                estrella.className =
                    i <= calificacion
                        ? "fas fa-star"
                        : "far fa-star";

                estrella.setAttribute("aria-hidden", "true");
                estrellas.appendChild(estrella);
            }

            const comentario = document.createElement("p");
            comentario.className = "testimonio-texto";
            comentario.textContent = `“${item.comentario || ""}”`;

            const autor = document.createElement("p");
            autor.className = "testimonio-autor";
            autor.textContent = item.nombre || "Cliente";

            tarjeta.append(estrellas, comentario, autor);
            columna.appendChild(tarjeta);
            fila.appendChild(columna);

            // Se observa después de insertar la tarjeta en el documento.
            lista.appendChild(fila);
            observarTarjeta(tarjeta);

            return fila;
        }

        // Carga el siguiente grupo de cinco reseñas.
        botonMas.addEventListener("click", async function () {
            if (cargando) return;

            cargando = true;
            botonMas.disabled = true;
            botonMas.textContent = "Cargando reseñas...";

            try {
                const url = new URL(window.location.href);
                url.searchParams.set("fragment", "1");
                url.searchParams.set("page", String(pagina));

                const respuesta = await fetch(url.toString(), {
                    method: "GET",
                    headers: {
                        "X-Requested-With": "XMLHttpRequest",
                        "Accept": "application/json"
                    }
                });

                if (!respuesta.ok) {
                    throw new Error(
                        `Error del servidor: ${respuesta.status}`
                    );
                }

                const datos = await respuesta.json();

                if (!Array.isArray(datos.items)) {
                    throw new Error(
                        "La respuesta no contiene una lista de reseñas."
                    );
                }

                total = Number(datos.total ?? total);

                datos.items.forEach(function (item) {
                    crearTarjeta(item);
                });

                mostradas += datos.items.length;

                if (datos.items.length > 0) {
                    pagina = Number(datos.next_page || pagina + 1);
                }

                actualizarContador();
                actualizarBotones(Boolean(datos.has_more));

                if (datos.items.length === 0 && datos.has_more) {
                    throw new Error(
                        "No se recibieron reseñas para esta página."
                    );
                }
            } catch (error) {
                console.error(
                    "Error al cargar los testimonios:",
                    error
                );

                alert(
                    "No se pudieron cargar las reseñas. " +
                    "Inténtalo de nuevo."
                );
            } finally {
                cargando = false;
                botonMas.disabled = false;
                botonMas.innerHTML =
                    '<span>Ver más reseñas</span> ' +
                    '<i class="fas fa-chevron-down" aria-hidden="true"></i>';
            }
        });

        // Oculta las reseñas adicionales y vuelve a la primera página.
        if (botonMenos) {
            botonMenos.addEventListener("click", function () {
                const tarjetas = Array.from(
                    lista.querySelectorAll(".testimonio-item")
                );

                tarjetas.slice(5).forEach(function (tarjeta) {
                    tarjeta.remove();
                });

                // Compatibilidad con tarjetas que no usan .testimonio-item.
                const restantes = Array.from(
                    lista.querySelectorAll(".testimonio-card")
                );

                restantes.slice(5).forEach(function (tarjeta) {
                    const fila = tarjeta.closest(".testimonio-item");
                    if (fila) {
                        fila.remove();
                    } else {
                        tarjeta.remove();
                    }
                });

                mostradas = lista.querySelectorAll(
                    ".testimonio-card"
                ).length;

                pagina = 2;

                actualizarContador();
                actualizarBotones(total > mostradas);

                const primera = lista.querySelector(".testimonio-card");

                if (primera) {
                    primera.scrollIntoView({
                        behavior: reducirMovimiento ? "auto" : "smooth",
                        block: "start"
                    });
                }
            });
        }

        actualizarContador();

        // Selector de estrellas del formulario, si existe.
        const selector = document.getElementById("selectorEstrellas");
        const campoCalificacion = document.getElementById(
            "id_calificacion"
        );

        if (selector && campoCalificacion) {
            selector.querySelectorAll(".estrella-btn").forEach(
                function (estrella) {
                    estrella.addEventListener("click", function () {
                        const valor = Number(this.dataset.valor);

                        campoCalificacion.value = valor;

                        selector.querySelectorAll(
                            ".estrella-btn"
                        ).forEach(function (item) {
                            const icono = item.querySelector("i");
                            if (!icono) return;

                            const activa =
                                Number(item.dataset.valor) <= valor;

                            icono.classList.toggle("fas", activa);
                            icono.classList.toggle("far", !activa);
                        });
                    });
                }
            );
        }
    }

    if (document.readyState === "loading") {
        document.addEventListener(
            "DOMContentLoaded",
            iniciarTestimonios
        );
    } else {
        iniciarTestimonios();
    }
})();
