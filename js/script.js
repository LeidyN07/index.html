const form = document.getElementById("formRegistro");
const lista = document.getElementById("lista");
const mensaje = document.getElementById("mensaje");
const total = document.getElementById("total");

let contador = 0;

form.addEventListener("submit", function (e) {
    e.preventDefault();

    const nombre = document.getElementById("nombre").value.trim();
    const descripcion = document.getElementById("descripcion").value.trim();
    const categoria = document.getElementById("categoria").value.trim();

    // VALIDACIÓN
    if (nombre === "" || descripcion === "" || categoria === "") {
        mensaje.innerHTML = `
            <div class="alert alert-danger">
                Todos los campos son obligatorios
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
            <h5>${nombre}</h5>
            <p>${descripcion}</p>
            <span class="badge bg-primary">${categoria}</span>

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
});