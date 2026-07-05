const form = document.getElementById("formRegistro");
const lista = document.getElementById("lista");
const mensaje = document.getElementById("mensaje");
const total = document.getElementById("total");

let contador = 0;


// VALIDACIÓN EN TIEMPO REAL


const nombre = document.getElementById("nombre");
const descripcion = document.getElementById("descripcion");
const categoria = document.getElementById("categoria");

nombre.addEventListener("input", validarNombre);
descripcion.addEventListener("input", validarDescripcion);
categoria.addEventListener("change", validarCategoria);

// -----------------------

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

function validarCategoria() {
    if (categoria.value === "") {
        categoria.classList.add("is-invalid");
        categoria.classList.remove("is-valid");
        return false;
    } else {
        categoria.classList.add("is-valid");
        categoria.classList.remove("is-invalid");
        return true;
    }
}

SUBMIT DEL FORMULARIO


form.addEventListener("submit", function (e) {
    e.preventDefault();

    const vNombre = validarNombre();
    const vDescripcion = validarDescripcion();
    const vCategoria = validarCategoria();

    if (!vNombre || !vDescripcion || !vCategoria) {
        mensaje.innerHTML = `
            <div class="alert alert-danger">
                Completa correctamente todos los campos
            </div>
        `;
        return;
    }

    mensaje.innerHTML = `
        <div class="alert alert-success">
            Registro agregado correctamente
        </div>
    `;

    // CREAR ELEMENTO
    const card = document.createElement("div");
    card.className = "card mb-3 shadow";

    card.innerHTML = `
        <div class="card-body">
            <h5>${nombre.value}</h5>
            <p>${descripcion.value}</p>
            <span class="badge bg-primary">${categoria.value}</span>

            <button class="btn btn-danger btn-sm float-end eliminar">
                Eliminar
            </button>
        </div>
    `;

    // ELIMINAR
    card.querySelector(".eliminar").addEventListener("click", function () {
        card.remove();
        contador--;
        total.textContent = contador;
    });

    lista.appendChild(card);

    contador++;
    total.textContent = contador;

    form.reset();

    // limpiar estilos
    nombre.classList.remove("is-valid");
    descripcion.classList.remove("is-valid");
    categoria.classList.remove("is-valid");
});ntent = contador;

    form.reset();
});
