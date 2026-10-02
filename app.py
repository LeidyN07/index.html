from flask import Flask, render_template, redirect, url_for, flash
import sqlite3
import os

from forms.producto_form import ProductoForm


app = Flask(__name__)
app.config['SECRET_KEY'] = 'tecnoayuda-clave-segura'

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE = os.path.join(BASE_DIR, 'data', 'tecnoayuda.db')


def crear_base_datos():
    """Crear la carpeta data y la tabla de servicios."""

    os.makedirs(
        os.path.join(BASE_DIR, 'data'),
        exist_ok=True
    )

    conn = sqlite3.connect(DATABASE)

    try:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS productos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                descripcion TEXT NOT NULL,
                precio REAL NOT NULL CHECK (precio >= 0)
            )
        ''')

        conn.commit()

    finally:
        conn.close()


@app.route('/')
def inicio():
    return render_template('index.html')


@app.route('/productos')
def productos():
    """Consultar los servicios registrados."""

    conn = sqlite3.connect(DATABASE)

    try:
        servicios = conn.execute(
            'SELECT id, nombre, descripcion, precio '
            'FROM productos ORDER BY id DESC'
        ).fetchall()

    finally:
        conn.close()

    return render_template(
        'productos.html',
        productos=servicios
    )


@app.route('/productos/nuevo', methods=['GET', 'POST'])
def nuevo_producto():
    """Validar y guardar un servicio."""

    form = ProductoForm()

    if form.validate_on_submit():
        conn = sqlite3.connect(DATABASE)

        try:
            conn.execute(
                '''
                INSERT INTO productos
                    (nombre, descripcion, precio)
                VALUES (?, ?, ?)
                ''',
                (
                    form.nombre.data,
                    form.descripcion.data,
                    float(form.precio.data)
                )
            )

            conn.commit()

        finally:
            conn.close()

        flash(
            'Servicio registrado correctamente.',
            'success'
        )

        return redirect(url_for('productos'))

    return render_template(
        'formulario_producto.html',
        form=form
    )


# Preparar la base también cuando Flask importe este archivo.
crear_base_datos()


if __name__ == '__main__':
    app.run(debug=True)
