const form = document.getElementById("formRegistro");
const lista = document.getElementById("lista");
const mensaje = document.getElementById("mensaje");
const total = document.getElementById("total");
const spinner = document.getElementById("spinner");

let contador = 0;

// CAMPOS
const nombre = document.getElementById("nombre");
const descripcion = document.getElementById("descripcion");
const categoria = document.getElementById("categoria");

// VALIDACIONES EN TIEMPO REAL
nombre.addEventListener("input", validarNombre);
descripcion.addEventListener("input", validarDescripcion);
categoria.addEventListener("input", validarCategoria);

// VALIDAR NOMBRE
function validarNombre() {
    if (nombre.value.trim().length < 3) {
        nombre.classList.add("is-invalid");
        nombre.classList.remove("is-valid");
        return false;
    } else {
        nombre.classList.add("is-valid");
        nombre.classList.remove("is-invalid");
        return true;
    }
}

// VALIDAR DESCRIPCIÓN
function validarDescripcion() {
    if (descripcion.value.trim().length < 5) {
        descripcion.classList.add("is-invalid");
        descripcion.classList.remove("is-valid");
        return false;
    } else {
        descripcion.classList.add("is-valid");
        descripcion.classList.remove("is-invalid");
        return true;
    }
}

// VALIDAR CATEGORÍA
function validarCategoria() {
    if (categoria.value.trim() === "") {
        categoria.classList.add("is-invalid");
        categoria.classList.remove("is-valid");
        return false;
    } else {
        categoria.classList.add("is-valid");
        categoria.classList.remove("is-invalid");
        return true;
    }
}

// ENVÍO DEL FORMULARIO
form.addEventListener("submit", function (e) {
    e.preventDefault();

    const vNombre = validarNombre();
    const vDescripcion = validarDescripcion();
    const vCategoria = validarCategoria();

    if (!vNombre || !vDescripcion || !vCategoria) {
        mensaje.innerHTML = `
            <div class="alert alert-danger alert-dismissible fade show" role="alert">
                Complete correctamente todos los campos.
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `;
        return;
    }

    // Mostrar spinner
    spinner.style.display = "block";

    setTimeout(() => {

        spinner.style.display = "none";

        mensaje.innerHTML = `
            <div class="alert alert-success alert-dismissible fade show" role="alert">
                Registro agregado correctamente.
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `;

        const card = document.createElement("div");
        card.className = "col-12";

        card.innerHTML = `
            <div class="card shadow h-100">
                <div class="card-body">

                    <h5 class="card-title">${nombre.value}</h5>

                    <p class="card-text">${descripcion.value}</p>

                    <span class="badge bg-primary">${categoria.value}</span>

                    <button class="btn btn-danger btn-sm float-end eliminar">
                        Eliminar
                    </button>

                </div>
            </div>
        `;

        card.querySelector(".eliminar").addEventListener("click", function () {
            card.remove();
            contador--;
            total.textContent = contador;
        });

        lista.appendChild(card);

        contador++;
        total.textContent = contador;

        form.reset();

        nombre.classList.remove("is-valid");
        descripcion.classList.remove("is-valid");
        categoria.classList.remove("is-valid");

    }, 1500);
});
