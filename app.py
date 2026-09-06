from flask import Flask, render_template, redirect, url_for, flash
import sqlite3
import os

from forms.producto_form import ProductoForm

app = Flask(__name__)
app.config['SECRET_KEY'] = 'tecnoayuda-clave-segura'

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE = os.path.join(BASE_DIR, 'data', 'ferreteria.db')


def crear_base_datos():
    os.makedirs(os.path.join(BASE_DIR, 'data'), exist_ok=True)

    conn = sqlite3.connect(DATABASE)

    conn.execute('''
        CREATE TABLE IF NOT EXISTS productos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            descripcion TEXT NOT NULL,
            precio REAL NOT NULL
        )
    ''')

    conn.commit()
    conn.close()


@app.route('/')
def inicio():
    return render_template('index.html')


@app.route('/productos')
def productos():
    conn = sqlite3.connect(DATABASE)

    productos = conn.execute(
        'SELECT * FROM productos'
    ).fetchall()

    conn.close()

    return render_template(
        'productos.html',
        productos=productos
    )


@app.route('/productos/nuevo', methods=['GET', 'POST'])
def nuevo_producto():
    form = ProductoForm()

    if form.validate_on_submit():

        conn = sqlite3.connect(DATABASE)

        conn.execute(
            'INSERT INTO productos (nombre, descripcion, precio) VALUES (?, ?, ?)',
            (
                form.nombre.data,
                form.descripcion.data,
                float(form.precio.data)
            )
        )

        conn.commit()
        conn.close()

        flash('Servicio registrado correctamente.', 'success')

        return redirect(url_for('productos'))

    return render_template(
        'formulario_producto.html',
        form=form
    )


if __name__ == '__main__':
    crear_base_datos()
    app.run(debug=True)