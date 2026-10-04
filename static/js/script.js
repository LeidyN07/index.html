document.addEventListener("DOMContentLoaded", function () {
    const form = document.getElementById("formRegistro");

    if (!form) {
        return;
    }

    const nombre = document.getElementById("nombre");
    const descripcion = document.getElementById("descripcion");
    const categoria = document.getElementById("categoria");
    const spinner = document.getElementById("spinner");
    const boton = form.querySelector('button[type="submit"]');

    if (!nombre || !descripcion || !categoria || !boton) {
        return;
    }

    // FORMULARIO CONECTADO CON FLASK
    if (form.dataset.modo === "servidor") {
        let enviando = false;

        form.addEventListener("submit", function (evento) {
            if (enviando) {
                evento.preventDefault();
                return;
            }

            if (!form.checkValidity()) {
                evento.preventDefault();
                form.reportValidity();
                return;
            }

            enviando = true;
            boton.disabled = true;
            form.setAttribute("aria-busy", "true");

            if (spinner) {
                spinner.style.display = "block";
            }

            // Permitir el envío normal del formulario a Python.
            // Los campos permanecen habilitados para enviar sus datos.
        });

        window.addEventListener("pageshow", function () {
            enviando = false;
            boton.disabled = false;
            form.setAttribute("aria-busy", "false");

            if (spinner) {
                spinner.style.display = "none";
            }
        });

        return;
    }

    // DEMOSTRACIÓN ESTÁTICA DE GITHUB PAGES
    const lista = document.getElementById("lista");
    const mensaje = document.getElementById("mensaje");
    const total = document.getElementById("total");

    if (!lista || !mensaje || !total) {
        return;
    }

    let contador = lista.children.length;
    total.textContent = contador;

    function mostrarMensaje(texto, tipo) {
        const alerta = document.createElement("div");

        alerta.className = `alert alert-${tipo}`;
        alerta.setAttribute("role", "status");
        alerta.textContent = texto;

        mensaje.replaceChildren(alerta);
    }

    function validarCampo(campo, valido) {
        campo.classList.toggle("is-invalid", !valido);
        campo.classList.toggle("is-valid", valido);

        return valido;
    }

    function agregarSolicitud(datos) {
        const tarjeta = document.createElement("div");
        tarjeta.className = "card shadow-sm mb-3";

        const cuerpo = document.createElement("div");
        cuerpo.className = "card-body";

        const titulo = document.createElement("h3");
        titulo.className = "h5";
        titulo.textContent = datos.nombre;

        const detalle = document.createElement("p");
        detalle.textContent = datos.descripcion;

        const etiqueta = document.createElement("span");
        etiqueta.className = "badge bg-primary";
        etiqueta.textContent = datos.categoria;

        const eliminar = document.createElement("button");
        eliminar.type = "button";
        eliminar.className = "btn btn-outline-danger btn-sm ms-3";
        eliminar.textContent = "Eliminar";

        eliminar.addEventListener("click", function () {
            tarjeta.remove();
            contador--;
            total.textContent = contador;
        });

        cuerpo.append(titulo, detalle, etiqueta, eliminar);
        tarjeta.appendChild(cuerpo);
        lista.appendChild(tarjeta);

        contador++;
        total.textContent = contador;
    }

    form.addEventListener("submit", function (evento) {
        evento.preventDefault();

        const nombreValido = validarCampo(
            nombre,
            nombre.value.trim().length >= 3 &&
            nombre.value.trim().length <= 100
        );

        const descripcionValida = validarCampo(
            descripcion,
            descripcion.value.trim().length >= 5 &&
            descripcion.value.trim().length <= 300
        );

        const categoriaValida = validarCampo(
            categoria,
            categoria.value.trim() !== ""
        );

        if (!nombreValido || !descripcionValida || !categoriaValida) {
            mostrarMensaje(
                "Revisa el nombre, la descripción y la categoría.",
                "danger"
            );
            return;
        }

        agregarSolicitud({
            nombre: nombre.value.trim(),
            descripcion: descripcion.value.trim(),
            categoria: categoria.value.trim()
        });

        mostrarMensaje(
            "Solicitud agregada a la demostración. " +
            "No se envía y desaparecerá al recargar.",
            "info"
        );

        form.reset();

        [nombre, descripcion, categoria].forEach(function (campo) {
            campo.classList.remove("is-valid", "is-invalid");
        });
    });
});