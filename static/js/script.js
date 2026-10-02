document.addEventListener("DOMContentLoaded", function () {
    const form = document.getElementById("formRegistro");
    const lista = document.getElementById("lista");
    const mensaje = document.getElementById("mensaje");
    const total = document.getElementById("total");
    const spinner = document.getElementById("spinner");

    const nombre = document.getElementById("nombre");
    const descripcion = document.getElementById("descripcion");
    const categoria = document.getElementById("categoria");

    // Ejecutar solamente si existe el formulario completo.
    if (
        !form || !lista || !mensaje || !total || !spinner ||
        !nombre || !descripcion || !categoria
    ) {
        return;
    }

    const botonRegistrar = form.querySelector('button[type="submit"]');

    let contador = 0;
    let procesando = false;

    // Usar nuestras validaciones al enviar el formulario.
    form.noValidate = true;
    total.textContent = contador;

    // Mostrar si un campo es válido.
    function marcarCampo(campo, valido) {
        campo.classList.toggle("is-valid", valido);
        campo.classList.toggle("is-invalid", !valido);
        campo.setAttribute("aria-invalid", String(!valido));

        return valido;
    }

    function validarNombre() {
        return marcarCampo(
            nombre,
            nombre.value.trim().length >= 3
        );
    }

    function validarDescripcion() {
        return marcarCampo(
            descripcion,
            descripcion.value.trim().length >= 5
        );
    }

    function validarCategoria() {
        return marcarCampo(
            categoria,
            categoria.value.trim().length > 0
        );
    }

    // Validaciones mientras se escribe.
    nombre.addEventListener("input", validarNombre);
    descripcion.addEventListener("input", validarDescripcion);
    categoria.addEventListener("input", validarCategoria);

    // Mostrar mensajes.
    function mostrarMensaje(texto, tipo) {
        const alerta = document.createElement("div");

        alerta.className =
            `alert alert-${tipo} alert-dismissible fade show`;
        alerta.setAttribute("role", "alert");

        const contenido = document.createElement("span");
        contenido.textContent = texto;

        const cerrar = document.createElement("button");
        cerrar.type = "button";
        cerrar.className = "btn-close";
        cerrar.setAttribute("data-bs-dismiss", "alert");
        cerrar.setAttribute("aria-label", "Cerrar mensaje");

        alerta.append(contenido, cerrar);
        mensaje.replaceChildren(alerta);
    }

    // Crear una tarjeta con los datos de la solicitud.
    function agregarSolicitud(datos) {
        const tarjeta = document.createElement("div");
        tarjeta.className = "card shadow mb-3";

        const cuerpo = document.createElement("div");
        cuerpo.className = "card-body";

        const titulo = document.createElement("h5");
        titulo.className = "card-title";
        titulo.textContent = datos.nombre;

        const detalle = document.createElement("p");
        detalle.className = "card-text";
        detalle.textContent = datos.descripcion;

        const etiqueta = document.createElement("span");
        etiqueta.className = "badge bg-primary";
        etiqueta.textContent = datos.categoria;

        const eliminar = document.createElement("button");
        eliminar.type = "button";
        eliminar.className =
            "btn btn-danger btn-sm float-end eliminar";
        eliminar.textContent = "Eliminar";

        eliminar.addEventListener("click", function () {
            tarjeta.remove();

            contador--;
            total.textContent = contador;

            mostrarMensaje(
                "Solicitud eliminada de la lista.",
                "info"
            );
        });

        cuerpo.append(titulo, detalle, etiqueta, eliminar);
        tarjeta.appendChild(cuerpo);
        lista.appendChild(tarjeta);

        contador++;
        total.textContent = contador;
    }

    // Enviar el formulario.
    form.addEventListener("submit", function (evento) {
        evento.preventDefault();

        if (procesando) {
            return;
        }

        const nombreValido = validarNombre();
        const descripcionValida = validarDescripcion();
        const categoriaValida = validarCategoria();

        if (
            !nombreValido ||
            !descripcionValida ||
            !categoriaValida
        ) {
            mostrarMensaje(
                "Escribe un nombre de al menos 3 caracteres, " +
                "una descripción de al menos 5 caracteres " +
                "y una categoría.",
                "danger"
            );

            const primerCampoInvalido =
                form.querySelector(".is-invalid");

            if (primerCampoInvalido) {
                primerCampoInvalido.focus();
            }

            return;
        }

        // Guardar los valores antes de mostrar la espera.
        const datos = {
            nombre: nombre.value.trim(),
            descripcion: descripcion.value.trim(),
            categoria: categoria.value.trim()
        };

        procesando = true;
        botonRegistrar.disabled = true;

        nombre.disabled = true;
        descripcion.disabled = true;
        categoria.disabled = true;

        mensaje.replaceChildren();
        spinner.style.display = "block";
        form.setAttribute("aria-busy", "true");

        // Simular el procesamiento visual de la solicitud.
        setTimeout(function () {
            agregarSolicitud(datos);

            spinner.style.display = "none";
            form.setAttribute("aria-busy", "false");

            mostrarMensaje(
                "Solicitud agregada a la lista de esta página.",
                "success"
            );

            form.reset();

            [nombre, descripcion, categoria].forEach(
                function (campo) {
                    campo.disabled = false;
                    campo.classList.remove(
                        "is-valid",
                        "is-invalid"
                    );
                    campo.removeAttribute("aria-invalid");
                }
            );

            procesando = false;
            botonRegistrar.disabled = false;
            nombre.focus();
        }, 1500);
    });
});
