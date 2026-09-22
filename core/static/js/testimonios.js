document.addEventListener("DOMContentLoaded", function () {

    const selector = document.getElementById("selectorEstrellas");
    const campoCalificacion = document.getElementById("id_calificacion");

    if (!selector || !campoCalificacion) {
        return;
    }

    const estrellas = selector.querySelectorAll(".estrella-btn");

    estrellas.forEach(function (estrella) {

        estrella.addEventListener("click", function () {

            const valor = parseInt(this.dataset.valor);

            campoCalificacion.value = valor;

            estrellas.forEach(function (item) {

                const numero = parseInt(item.dataset.valor);
                const icono = item.querySelector("i");

                if (numero <= valor) {
                    icono.classList.remove("far");
                    icono.classList.add("fas");
                } else {
                    icono.classList.remove("fas");
                    icono.classList.add("far");
                }

            });

        });

    });

});