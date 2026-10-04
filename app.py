from flask import (
    Flask, render_template, redirect, url_for, flash,
    session, abort, request, send_file
)
from flask_wtf import FlaskForm
from flask_login import (
    LoginManager, UserMixin, current_user,
    login_user, logout_user, login_required
)
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import timedelta
from decimal import Decimal, ROUND_HALF_UP
from getpass import getpass
from io import BytesIO
from dotenv import load_dotenv
from psycopg.rows import dict_row

import mimetypes
import psycopg
import secrets
import os
import sys

from database import conectar, crear_base_datos

from forms.producto_form import ProductoForm
from forms.login_form import LoginForm
from forms.solicitud_form import SolicitudForm
from forms.cliente_form import ClienteForm
from forms.proveedor_form import ProveedorForm
from forms.facturacion_form import FacturacionForm
from forms.pedido_form import PedidoForm
from forms.gestion_pedido_form import GestionPedidoForm
from forms.cuenta_cliente_form import RegistroClienteForm, LoginClienteForm


# CONFIGURACIÓN

load_dotenv()

app = Flask(__name__)

clave_sesion = os.environ.get("SECRET_KEY")

if not clave_sesion or len(clave_sesion) < 32:
    raise RuntimeError(
        "Configura SECRET_KEY con al menos 32 caracteres en .env o Render."
    )

app.config["SECRET_KEY"] = clave_sesion
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(minutes=30)
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = os.environ.get("RENDER") == "true"

MAX_ARCHIVO = 10 * 1024 * 1024
app.config["MAX_CONTENT_LENGTH"] = MAX_ARCHIVO + 1024 * 1024

login_manager = LoginManager(app)


# CONSULTAS A POSTGRESQL

def consultar(sql, parametros=(), uno=False):
    conn = conectar()

    try:
        resultado = conn.execute(sql, parametros)

        if uno:
            return resultado.fetchone()

        return resultado.fetchall()

    finally:
        conn.close()


def guardar(sql, parametros):
    conn = conectar()

    try:
        cursor = conn.execute(sql, parametros)
        resultado = cursor.fetchone() if cursor.description else None

        conn.commit()

        return resultado[0] if resultado else None

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()


def calcular_importes(precio, cantidad):
    precio = Decimal(str(precio)).quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP
    )

    total = (precio * cantidad).quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP
    )

    return precio, total


# AUTENTICACIÓN

class Usuario(UserMixin):
    def __init__(self, rol, identificador):
        self.rol = rol
        self.identificador = int(identificador)
        self.id = f"{rol}:{self.identificador}"


@login_manager.user_loader
def cargar_usuario(identificador):
    try:
        rol, numero = identificador.split(":", 1)
        numero = int(numero)

    except (ValueError, AttributeError):
        return None

    if rol == "admin":
        registro = consultar(
            "SELECT id FROM administradores WHERE id = %s",
            (numero,),
            uno=True
        )

    elif rol == "cliente":
        registro = consultar(
            "SELECT id FROM cuentas_clientes WHERE id = %s",
            (numero,),
            uno=True
        )

    else:
        return None

    return Usuario(rol, numero) if registro else None


@login_manager.unauthorized_handler
def acceso_sin_sesion():
    session.pop("administrador", None)
    session.pop("cuenta_cliente_id", None)

    es_cliente = request.path.startswith("/cliente/")

    flash("Inicia sesión para continuar.", "warning")

    return redirect(
        url_for("login_cliente" if es_cliente else "login")
    )


@app.before_request
def sincronizar_identidad():
    if current_user.is_authenticated:
        if current_user.rol == "admin":
            session.pop("cuenta_cliente_id", None)

            registro = consultar(
                "SELECT usuario FROM administradores WHERE id = %s",
                (current_user.identificador,),
                uno=True
            )

            session["administrador"] = registro[0]

        else:
            session.pop("administrador", None)
            session["cuenta_cliente_id"] = current_user.identificador

    else:
        session.pop("administrador", None)
        session.pop("cuenta_cliente_id", None)


def acceso_requerido(funcion):
    @wraps(funcion)
    def verificar(*args, **kwargs):
        if (
            not current_user.is_authenticated
            or current_user.rol != "admin"
        ):
            abort(403)

        return funcion(*args, **kwargs)

    return verificar


def obtener_cliente_actual():
    cuenta_id = session.get("cuenta_cliente_id")

    if not cuenta_id:
        return None

    return consultar(
        """
        SELECT c.id, c.nombre, cc.correo, c.telefono
        FROM cuentas_clientes AS cc
        JOIN clientes AS c ON c.id = cc.cliente_id
        WHERE cc.id = %s
        """,
        (cuenta_id,),
        uno=True
    )


def cliente_requerido(funcion):
    @wraps(funcion)
    def verificar(*args, **kwargs):
        if (
            not current_user.is_authenticated
            or current_user.rol != "cliente"
        ):
            abort(403)

        if obtener_cliente_actual() is None:
            logout_user()
            session.clear()

            return redirect(url_for("login_cliente"))

        return funcion(*args, **kwargs)

    return verificar


# CREAR O RESTABLECER LA CUENTA ADMINISTRADORA

def preparar_administrador():
    usuario = os.environ.get("ADMIN_USUARIO", "").strip()
    clave = os.environ.get("ADMIN_CLAVE", "")

    if not usuario and not clave:
        return

    if not usuario or len(usuario) > 50 or len(clave) < 12:
        raise RuntimeError(
            "ADMIN_USUARIO debe tener entre 1 y 50 caracteres "
            "y ADMIN_CLAVE al menos 12."
        )

    restablecer = (
        os.environ.get("ADMIN_RESTABLECER", "").strip().lower() == "true"
    )

    if restablecer:
        sql = """
            INSERT INTO administradores (id, usuario, clave_hash)
            VALUES (%s, %s, %s)
            ON CONFLICT (id) DO UPDATE
            SET usuario = EXCLUDED.usuario,
                clave_hash = EXCLUDED.clave_hash
            RETURNING id
        """

    else:
        sql = """
            INSERT INTO administradores (id, usuario, clave_hash)
            VALUES (%s, %s, %s)
            ON CONFLICT (id) DO NOTHING
            RETURNING id
        """

    guardar(
        sql,
        (1, usuario, generate_password_hash(clave))
    )


def crear_administrador():
    existente = consultar(
        "SELECT id FROM administradores WHERE id = 1",
        uno=True
    )

    if existente:
        print("Ya existe una cuenta de administración.")
        return

    usuario = input("Elige tu usuario: ").strip()

    if not usuario or len(usuario) > 50:
        print("El usuario debe tener entre 1 y 50 caracteres.")
        return

    clave = getpass("Elige una contraseña de al menos 12 caracteres: ")
    confirmar = getpass("Repite la contraseña: ")

    if len(clave) < 12:
        print("La contraseña debe tener al menos 12 caracteres.")
        return

    if clave != confirmar:
        print("Las contraseñas no coinciden.")
        return

    guardar(
        """
        INSERT INTO administradores (id, usuario, clave_hash)
        VALUES (%s, %s, %s)
        """,
        (1, usuario, generate_password_hash(clave))
    )

    print("Cuenta de administración creada correctamente.")


# PÁGINA PRINCIPAL

@app.route("/")
def inicio():
    return render_template(
        "index.html",
        form=SolicitudForm()
    )


# ACCESO DE ADMINISTRACIÓN

@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("administrador"):
        return redirect(url_for("productos"))

    form = LoginForm()

    if form.validate_on_submit():
        administrador = consultar(
            """
            SELECT usuario, clave_hash
            FROM administradores
            WHERE id = 1
            """,
            uno=True
        )

        if (
            administrador
            and form.usuario.data == administrador[0]
            and check_password_hash(
                administrador[1],
                form.clave.data
            )
        ):
            session.clear()
            login_user(Usuario("admin", 1))

            session["administrador"] = administrador[0]
            session.permanent = True

            flash(
                "Bienvenida a la administración de TecnoAyuda.",
                "success"
            )

            return redirect(url_for("productos"))

        flash("Usuario o contraseña incorrectos.", "danger")

    return render_template("login.html", form=form)


@app.route("/logout", methods=["GET", "POST"])
@login_required
@acceso_requerido
def logout():
    form = FlaskForm()

    if form.validate_on_submit():
        logout_user()
        session.clear()

        flash("Cerraste sesión correctamente.", "success")

        return redirect(url_for("inicio"))

    return render_template("logout.html", form=form)


# CUENTAS DE CLIENTES

@app.route("/cliente/registro", methods=["GET", "POST"])
def registro_cliente():
    if obtener_cliente_actual():
        return redirect(url_for("mi_cuenta"))

    form = RegistroClienteForm()

    if form.validate_on_submit():
        conn = conectar()

        try:
            cursor = conn.execute(
                """
                INSERT INTO clientes (nombre, correo, telefono)
                VALUES (%s, %s, %s)
                RETURNING id
                """,
                (
                    form.nombre.data,
                    form.correo.data,
                    form.telefono.data
                )
            )

            cliente_id = cursor.fetchone()[0]

            cursor = conn.execute(
                """
                INSERT INTO cuentas_clientes
                    (cliente_id, correo, clave_hash)
                VALUES (%s, %s, %s)
                RETURNING id
                """,
                (
                    cliente_id,
                    form.correo.data,
                    generate_password_hash(form.clave.data)
                )
            )

            cuenta_id = cursor.fetchone()[0]

            conn.commit()

        except psycopg.IntegrityError:
            conn.rollback()

            form.correo.errors.append(
                "No se pudo crear la cuenta con ese correo. "
                "Si ya tienes una cuenta, inicia sesión."
            )

        else:
            session.clear()
            login_user(Usuario("cliente", cuenta_id))

            session["cuenta_cliente_id"] = cuenta_id
            session.permanent = True

            flash("Tu cuenta se creó correctamente.", "success")

            return redirect(url_for("mi_cuenta"))

        finally:
            conn.close()

    return render_template("registro_cliente.html", form=form)


@app.route("/cliente/login", methods=["GET", "POST"])
def login_cliente():
    if obtener_cliente_actual():
        return redirect(url_for("mi_cuenta"))

    form = LoginClienteForm()

    if form.validate_on_submit():
        cuenta = consultar(
            """
            SELECT id, clave_hash
            FROM cuentas_clientes
            WHERE correo = %s
            """,
            (form.correo.data,),
            uno=True
        )

        if cuenta and check_password_hash(
            cuenta[1],
            form.clave.data
        ):
            session.clear()
            login_user(Usuario("cliente", cuenta[0]))

            session["cuenta_cliente_id"] = cuenta[0]
            session.permanent = True

            flash("Ingresaste a tu cuenta correctamente.", "success")

            return redirect(url_for("mi_cuenta"))

        flash("Correo o contraseña incorrectos.", "danger")

    return render_template("login_cliente.html", form=form)


@app.route("/cliente/cuenta")
@login_required
@cliente_requerido
def mi_cuenta():
    return render_template(
        "mi_cuenta.html",
        cliente=obtener_cliente_actual(),
        form=FlaskForm()
    )


@app.route("/cliente/logout", methods=["POST"])
@login_required
@cliente_requerido
def logout_cliente():
    form = FlaskForm()

    if not form.validate_on_submit():
        abort(400)

    logout_user()
    session.clear()

    flash("Cerraste tu sesión de cliente.", "success")

    return redirect(url_for("inicio"))


# PEDIDOS DEL CLIENTE

@app.route(
    "/cliente/servicios/<int:servicio_id>/pedir",
    methods=["GET", "POST"]
)
@login_required
@cliente_requerido
def solicitar_servicio(servicio_id):
    cliente = obtener_cliente_actual()

    servicio = consultar(
        """
        SELECT id, nombre, descripcion, precio
        FROM productos
        WHERE id = %s
        """,
        (servicio_id,),
        uno=True
    )

    if servicio is None:
        abort(404)

    form = PedidoForm()

    if form.validate_on_submit():
        conn = conectar()

        try:
            conn.execute("BEGIN")

            servicio_actual = conn.execute(
                """
                SELECT id, nombre, descripcion, precio
                FROM productos
                WHERE id = %s
                """,
                (servicio_id,)
            ).fetchone()

            if servicio_actual is None:
                abort(404)

            precio, total = calcular_importes(
                servicio_actual[3],
                form.cantidad.data
            )

            cursor = conn.execute(
                """
                INSERT INTO facturacion (
                    cliente_id, producto_id, cantidad,
                    precio_unitario, total,
                    metodo_pago, referencia, estado
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
                """,
                (
                    cliente[0],
                    servicio_actual[0],
                    form.cantidad.data,
                    float(precio),
                    float(total),
                    "No indicado",
                    "",
                    "Pendiente"
                )
            )

            factura_id = cursor.fetchone()[0]

            conn.execute(
                """
                INSERT INTO pedidos (
                    cliente_id, producto_id, factura_id,
                    servicio, descripcion, estado_trabajo
                )
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id
                """,
                (
                    cliente[0],
                    servicio_actual[0],
                    factura_id,
                    servicio_actual[1],
                    form.descripcion.data,
                    "Recibido"
                )
            )

            conn.commit()

        except Exception:
            conn.rollback()
            raise

        finally:
            conn.close()

        flash(
            "Tu pedido se registró correctamente. El pago está pendiente.",
            "success"
        )

        return redirect(url_for("mis_pedidos"))

    return render_template(
        "formulario_pedido.html",
        servicio=servicio,
        form=form
    )


@app.route("/cliente/pedidos")
@login_required
@cliente_requerido
def mis_pedidos():
    cliente = obtener_cliente_actual()

    conn = conectar()
    conn.row_factory = dict_row

    try:
        pedidos = conn.execute(
            """
            SELECT
                p.id,
                p.servicio,
                p.descripcion,
                f.cantidad,
                f.total,
                f.estado AS estado_pago,
                p.estado_trabajo,
                p.observaciones,
                p.archivo_original,
                p.archivo_guardado,
                p.fecha
            FROM pedidos AS p
            JOIN facturacion AS f ON f.id = p.factura_id
            WHERE p.cliente_id = %s
            AND f.cliente_id = %s
            ORDER BY p.id DESC
            """,
            (cliente[0], cliente[0])
        ).fetchall()

    finally:
        conn.close()

    return render_template("mis_pedidos.html", pedidos=pedidos)


# CATÁLOGO DE SERVICIOS

@app.route("/productos")
def productos():
    servicios = consultar(
        """
        SELECT id, nombre, descripcion, precio
        FROM productos
        ORDER BY id DESC
        """
    )

    return render_template(
        "productos.html",
        productos=servicios
    )


@app.route("/productos/nuevo", methods=["GET", "POST"])
@login_required
@acceso_requerido
def nuevo_producto():
    form = ProductoForm()

    if form.validate_on_submit():
        guardar(
            """
            INSERT INTO productos (nombre, descripcion, precio)
            VALUES (%s, %s, %s)
            """,
            (
                form.nombre.data,
                form.descripcion.data,
                float(form.precio.data)
            )
        )

        flash("Servicio registrado correctamente.", "success")

        return redirect(url_for("productos"))

    return render_template("formulario_producto.html", form=form)


@app.route(
    "/productos/<int:servicio_id>/editar",
    methods=["GET", "POST"]
)
@login_required
@acceso_requerido
def editar_producto(servicio_id):
    servicio = consultar(
        """
        SELECT id, nombre, descripcion, precio
        FROM productos
        WHERE id = %s
        """,
        (servicio_id,),
        uno=True
    )

    if servicio is None:
        abort(404)

    form = ProductoForm()

    if request.method == "GET":
        form.nombre.data = servicio[1]
        form.descripcion.data = servicio[2]
        form.precio.data = Decimal(str(servicio[3]))

    if form.validate_on_submit():
        guardar(
            """
            UPDATE productos
            SET nombre = %s, descripcion = %s, precio = %s
            WHERE id = %s
            """,
            (
                form.nombre.data,
                form.descripcion.data,
                float(form.precio.data),
                servicio_id
            )
        )

        flash("Servicio actualizado correctamente.", "success")

        return redirect(url_for("productos"))

    return render_template("formulario_producto.html", form=form)


@app.route(
    "/productos/<int:servicio_id>/eliminar",
    methods=["GET", "POST"]
)
@login_required
@acceso_requerido
def eliminar_producto(servicio_id):
    servicio = consultar(
        """
        SELECT id, nombre, descripcion, precio
        FROM productos
        WHERE id = %s
        """,
        (servicio_id,),
        uno=True
    )

    if servicio is None:
        abort(404)

    form = FlaskForm()

    if form.validate_on_submit():
        conn = conectar()

        try:
            conn.execute(
                "DELETE FROM productos WHERE id = %s",
                (servicio_id,)
            )

            conn.commit()

        except psycopg.IntegrityError:
            conn.rollback()

            flash(
                "No puedes eliminar este servicio porque tiene pedidos "
                "o registros de facturación relacionados.",
                "warning"
            )

        except psycopg.Error:
            conn.rollback()

            app.logger.exception(
                "No se pudo eliminar el servicio %s",
                servicio_id
            )

            flash(
                "No se pudo eliminar el servicio. Intenta nuevamente.",
                "danger"
            )

        else:
            flash("Servicio eliminado correctamente.", "success")

        finally:
            conn.close()

        return redirect(url_for("productos"))

    return render_template(
        "eliminar_producto.html",
        servicio=servicio,
        form=form
    )


# SOLICITUDES DE CONTACTO

@app.route("/solicitudes/enviar", methods=["POST"])
def enviar_solicitud():
    form = SolicitudForm()

    if form.validate_on_submit():
        guardar(
            """
            INSERT INTO solicitudes (nombre, descripcion, categoria)
            VALUES (%s, %s, %s)
            """,
            (
                form.nombre.data,
                form.descripcion.data,
                form.categoria.data
            )
        )

        flash("Tu solicitud se guardó correctamente.", "success")

        return redirect(url_for("inicio", _anchor="registro"))

    flash(
        "No se guardó la solicitud. Revisa los campos del formulario.",
        "danger"
    )

    return render_template("index.html", form=form), 400


@app.route("/admin/solicitudes")
@login_required
@acceso_requerido
def solicitudes():
    registros = consultar(
        """
        SELECT id, nombre, descripcion, categoria, fecha
        FROM solicitudes
        ORDER BY id DESC
        """
    )

    return render_template(
        "solicitudes.html",
        solicitudes=registros
    )


# ADMINISTRACIÓN DE CLIENTES

@app.route("/admin/clientes")
@login_required
@acceso_requerido
def clientes():
    registros = consultar(
        """
        SELECT id, nombre, correo, telefono
        FROM clientes
        ORDER BY id DESC
        """
    )

    return render_template("clientes.html", clientes=registros)


@app.route("/admin/clientes/nuevo", methods=["GET", "POST"])
@login_required
@acceso_requerido
def nuevo_cliente():
    form = ClienteForm()

    if form.validate_on_submit():
        guardar(
            """
            INSERT INTO clientes (nombre, correo, telefono)
            VALUES (%s, %s, %s)
            """,
            (
                form.nombre.data,
                form.correo.data,
                form.telefono.data
            )
        )

        flash("Cliente registrado correctamente.", "success")

        return redirect(url_for("clientes"))

    return render_template("formulario_cliente.html", form=form)


@app.route(
    "/admin/clientes/<int:cliente_id>/editar",
    methods=["GET", "POST"]
)
@login_required
@acceso_requerido
def editar_cliente(cliente_id):
    cliente = consultar(
        """
        SELECT id, nombre, correo, telefono
        FROM clientes
        WHERE id = %s
        """,
        (cliente_id,),
        uno=True
    )

    if cliente is None:
        abort(404)

    cuenta = consultar(
        """
        SELECT id
        FROM cuentas_clientes
        WHERE cliente_id = %s
        """,
        (cliente_id,),
        uno=True
    )

    form = ClienteForm()

    if request.method == "GET":
        form.nombre.data = cliente[1]
        form.correo.data = cliente[2]
        form.telefono.data = cliente[3]

    if form.validate_on_submit():
        correo = form.correo.data.strip().lower()

        conn = conectar()

        try:
            conn.execute("BEGIN")

            conn.execute(
                """
                UPDATE clientes
                SET nombre = %s, correo = %s, telefono = %s
                WHERE id = %s
                """,
                (
                    form.nombre.data,
                    correo,
                    form.telefono.data,
                    cliente_id
                )
            )

            conn.execute(
                """
                UPDATE cuentas_clientes
                SET correo = %s
                WHERE cliente_id = %s
                """,
                (correo, cliente_id)
            )

            conn.commit()

        except psycopg.IntegrityError:
            conn.rollback()

            form.correo.errors.append(
                "Ese correo ya pertenece a otra cuenta. "
                "Utiliza un correo diferente."
            )

        except psycopg.Error:
            conn.rollback()

            app.logger.exception(
                "No se pudo editar el cliente %s",
                cliente_id
            )

            flash(
                "No se guardaron los cambios. Intenta nuevamente.",
                "danger"
            )

        else:
            flash("Cliente actualizado correctamente.", "success")

            return redirect(url_for("clientes"))

        finally:
            conn.close()

    return render_template(
        "formulario_cliente.html",
        form=form,
        editando=True,
        tiene_cuenta=bool(cuenta)
    )


@app.route(
    "/admin/clientes/<int:cliente_id>/eliminar",
    methods=["GET", "POST"]
)
@login_required
@acceso_requerido
def eliminar_cliente(cliente_id):
    cliente = consultar(
        """
        SELECT id, nombre, correo, telefono
        FROM clientes
        WHERE id = %s
        """,
        (cliente_id,),
        uno=True
    )

    if cliente is None:
        abort(404)

    form = FlaskForm()

    if form.validate_on_submit():
        conn = conectar()

        try:
            conn.execute(
                "DELETE FROM clientes WHERE id = %s",
                (cliente_id,)
            )

            conn.commit()

        except psycopg.IntegrityError:
            conn.rollback()

            flash(
                "No puedes eliminar este cliente porque tiene una cuenta, "
                "pedidos o registros de facturación relacionados.",
                "warning"
            )

        except psycopg.Error:
            conn.rollback()

            app.logger.exception(
                "No se pudo eliminar el cliente %s",
                cliente_id
            )

            flash(
                "No se pudo eliminar el cliente. Intenta nuevamente.",
                "danger"
            )

        else:
            flash("Cliente eliminado correctamente.", "success")

        finally:
            conn.close()

        return redirect(url_for("clientes"))

    return render_template(
        "eliminar_cliente.html",
        cliente=cliente,
        form=form
    )


# COLABORADORES

@app.route("/admin/proveedores")
@login_required
@acceso_requerido
def proveedores():
    registros = consultar(
        """
        SELECT id, nombre, contacto, servicio
        FROM proveedores
        ORDER BY id DESC
        """
    )

    return render_template(
        "proveedores.html",
        proveedores=registros
    )


@app.route("/admin/proveedores/nuevo", methods=["GET", "POST"])
@login_required
@acceso_requerido
def nuevo_proveedor():
    form = ProveedorForm()

    if form.validate_on_submit():
        guardar(
            """
            INSERT INTO proveedores (nombre, contacto, servicio)
            VALUES (%s, %s, %s)
            """,
            (
                form.nombre.data,
                form.contacto.data,
                form.servicio.data
            )
        )

        flash("Colaborador registrado correctamente.", "success")

        return redirect(url_for("proveedores"))

    return render_template("formulario_proveedor.html", form=form)


# FACTURACIÓN

@app.route("/admin/facturacion")
@login_required
@acceso_requerido
def facturacion():
    registros = consultar(
        """
        SELECT
            f.id, c.nombre, p.nombre, f.cantidad,
            f.precio_unitario, f.total, f.fecha,
            f.metodo_pago, f.referencia, f.estado, f.fecha_pago
        FROM facturacion AS f
        JOIN clientes AS c ON c.id = f.cliente_id
        JOIN productos AS p ON p.id = f.producto_id
        ORDER BY f.id DESC
        """
    )

    return render_template(
        "facturacion.html",
        facturas=registros
    )


@app.route("/admin/facturacion/nuevo", methods=["GET", "POST"])
@login_required
@acceso_requerido
def nueva_factura():
    form = FacturacionForm()

    clientes_registrados = consultar(
        "SELECT id, nombre FROM clientes ORDER BY nombre"
    )

    servicios_registrados = consultar(
        "SELECT id, nombre, precio FROM productos ORDER BY nombre"
    )

    form.cliente_id.choices = [
        (cliente[0], cliente[1])
        for cliente in clientes_registrados
    ]

    form.producto_id.choices = [
        (servicio[0], f"{servicio[1]} — ${servicio[2]:.2f}")
        for servicio in servicios_registrados
    ]

    disponible = bool(
        clientes_registrados and servicios_registrados
    )

    if disponible and form.validate_on_submit():
        servicio = consultar(
            "SELECT precio FROM productos WHERE id = %s",
            (form.producto_id.data,),
            uno=True
        )

        if servicio is None:
            flash("El servicio ya no está disponible.", "warning")

            return redirect(url_for("nueva_factura"))

        precio, total = calcular_importes(
            servicio[0],
            form.cantidad.data
        )

        estado = "Pagado" if form.pagado.data else "Pendiente"

        conn = conectar()

        try:
            conn.execute(
                """
                INSERT INTO facturacion (
                    cliente_id, producto_id, cantidad,
                    precio_unitario, total, metodo_pago,
                    referencia, estado, fecha_pago
                )
                VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s,
                    CASE WHEN %s = 'Pagado'
                    THEN (CURRENT_TIMESTAMP AT TIME ZONE 'UTC')::text
                    ELSE NULL END
                )
                RETURNING id
                """,
                (
                    form.cliente_id.data,
                    form.producto_id.data,
                    form.cantidad.data,
                    float(precio),
                    float(total),
                    form.metodo_pago.data,
                    form.referencia.data or "",
                    estado,
                    estado
                )
            )

            conn.commit()

        finally:
            conn.close()

        flash(f"Registro guardado con estado: {estado}.", "success")

        return redirect(url_for("facturacion"))

    return render_template(
        "formulario_facturacion.html",
        form=form,
        disponible=disponible
    )


@app.route(
    "/admin/facturacion/<int:registro_id>/pagar",
    methods=["GET", "POST"]
)
@login_required
@acceso_requerido
def confirmar_pago(registro_id):
    registro = consultar(
        """
        SELECT
            f.id, c.nombre, p.nombre, f.total, f.estado,
            f.metodo_pago, f.referencia
        FROM facturacion AS f
        JOIN clientes AS c ON c.id = f.cliente_id
        JOIN productos AS p ON p.id = f.producto_id
        WHERE f.id = %s
        """,
        (registro_id,),
        uno=True
    )

    if registro is None:
        abort(404)

    if registro[4] == "Pagado":
        flash("Este registro ya está pagado.", "info")

        return redirect(url_for("facturacion"))

    form = FacturacionForm()

    form.cliente_id.choices = []
    form.producto_id.choices = []

    if form.is_submitted():
        csrf_valido = form.csrf_token.validate(form)
        metodo_valido = form.metodo_pago.validate(form)
        referencia_valida = form.referencia.validate(form)

        if (
            csrf_valido
            and metodo_valido
            and referencia_valida
            and form.pagado.data
        ):
            guardar(
                """
                UPDATE facturacion
                SET estado = 'Pagado',
                    metodo_pago = %s,
                    referencia = %s,
                    fecha_pago =
                        (CURRENT_TIMESTAMP AT TIME ZONE 'UTC')::text
                WHERE id = %s AND estado = 'Pendiente'
                """,
                (
                    form.metodo_pago.data,
                    form.referencia.data or "",
                    registro_id
                )
            )

            flash("Pago confirmado correctamente.", "success")

            return redirect(url_for("facturacion"))

        flash(
            "Selecciona el método y confirma que recibiste el pago.",
            "warning"
        )

    else:
        if registro[5] in ["Efectivo", "Transferencia"]:
            form.metodo_pago.data = registro[5]

        form.referencia.data = registro[6]

    return render_template(
        "confirmar_pago.html",
        registro=registro,
        form=form
    )


@app.route(
    "/admin/facturacion/<int:registro_id>/editar",
    methods=["GET", "POST"]
)
@login_required
@acceso_requerido
def editar_factura(registro_id):
    registro = consultar(
        """
        SELECT id, cliente_id, producto_id, cantidad,
               precio_unitario, estado, metodo_pago, referencia
        FROM facturacion
        WHERE id = %s
        """,
        (registro_id,),
        uno=True
    )

    if registro is None:
        abort(404)

    pedido = consultar(
        "SELECT id FROM pedidos WHERE factura_id = %s",
        (registro_id,),
        uno=True
    )

    if registro[5] != "Pendiente" or pedido:
        flash(
            "Solo puedes editar registros pendientes "
            "que no estén vinculados a pedidos.",
            "warning"
        )

        return redirect(url_for("facturacion"))

    form = FacturacionForm()

    form.cliente_id.choices = [
        (fila[0], fila[1])
        for fila in consultar(
            "SELECT id, nombre FROM clientes ORDER BY nombre"
        )
    ]

    form.producto_id.choices = [
        (fila[0], f"{fila[1]} — ${fila[2]:.2f}")
        for fila in consultar(
            "SELECT id, nombre, precio FROM productos ORDER BY nombre"
        )
    ]

    disponible = bool(
        form.cliente_id.choices and form.producto_id.choices
    )

    if request.method == "GET":
        form.cliente_id.data = registro[1]
        form.producto_id.data = registro[2]
        form.cantidad.data = registro[3]

        if registro[6] in ("Efectivo", "Transferencia"):
            form.metodo_pago.data = registro[6]

        form.referencia.data = registro[7]
        form.pagado.data = False

    if disponible and form.validate_on_submit():
        if form.pagado.data:
            flash(
                "Guarda la edición primero. Para registrar el pago, "
                "utiliza después el botón Confirmar pago.",
                "warning"
            )

        else:
            conn = conectar()

            try:
                conn.execute("BEGIN")

                actual = conn.execute(
                    """
                    SELECT producto_id, precio_unitario, estado
                    FROM facturacion
                    WHERE id = %s
                    FOR UPDATE
                    """,
                    (registro_id,)
                ).fetchone()

                vinculado = conn.execute(
                    "SELECT id FROM pedidos WHERE factura_id = %s",
                    (registro_id,)
                ).fetchone()

                if actual is None:
                    abort(404)

                if actual[2] != "Pendiente" or vinculado:
                    conn.rollback()

                    flash("El registro ya no se puede editar.", "warning")

                    return redirect(url_for("facturacion"))

                servicio = conn.execute(
                    "SELECT precio FROM productos WHERE id = %s",
                    (form.producto_id.data,)
                ).fetchone()

                cliente = conn.execute(
                    "SELECT id FROM clientes WHERE id = %s",
                    (form.cliente_id.data,)
                ).fetchone()

                if servicio is None or cliente is None:
                    conn.rollback()

                    flash(
                        "El cliente o servicio ya no está disponible.",
                        "warning"
                    )

                    return redirect(
                        url_for(
                            "editar_factura",
                            registro_id=registro_id
                        )
                    )

                precio_base = (
                    actual[1]
                    if form.producto_id.data == actual[0]
                    else servicio[0]
                )

                precio, total = calcular_importes(
                    precio_base,
                    form.cantidad.data
                )

                conn.execute(
                    """
                    UPDATE facturacion
                    SET cliente_id = %s,
                        producto_id = %s,
                        cantidad = %s,
                        precio_unitario = %s,
                        total = %s,
                        metodo_pago = %s,
                        referencia = %s
                    WHERE id = %s
                    """,
                    (
                        form.cliente_id.data,
                        form.producto_id.data,
                        form.cantidad.data,
                        float(precio),
                        float(total),
                        form.metodo_pago.data,
                        form.referencia.data or "",
                        registro_id
                    )
                )

                conn.commit()

            except psycopg.Error:
                conn.rollback()

                app.logger.exception(
                    "No se pudo editar el registro %s",
                    registro_id
                )

                flash(
                    "No se guardaron los cambios. Intenta nuevamente.",
                    "danger"
                )

            else:
                flash("Registro actualizado correctamente.", "success")

                return redirect(url_for("facturacion"))

            finally:
                conn.close()

    return render_template(
        "formulario_facturacion.html",
        form=form,
        disponible=disponible,
        editando=True
    )


@app.route(
    "/admin/facturacion/<int:registro_id>/eliminar",
    methods=["GET", "POST"]
)
@login_required
@acceso_requerido
def eliminar_factura(registro_id):
    registro = consultar(
        """
        SELECT f.id, c.nombre, p.nombre, f.total, f.estado
        FROM facturacion AS f
        JOIN clientes AS c ON c.id = f.cliente_id
        JOIN productos AS p ON p.id = f.producto_id
        WHERE f.id = %s
        """,
        (registro_id,),
        uno=True
    )

    if registro is None:
        abort(404)

    pedido = consultar(
        "SELECT id FROM pedidos WHERE factura_id = %s",
        (registro_id,),
        uno=True
    )

    if registro[4] != "Pendiente" or pedido:
        flash(
            "Solo puedes eliminar registros pendientes "
            "que no estén vinculados a pedidos.",
            "warning"
        )

        return redirect(url_for("facturacion"))

    form = FlaskForm()

    if form.validate_on_submit():
        conn = conectar()

        try:
            cursor = conn.execute(
                """
                DELETE FROM facturacion
                WHERE id = %s
                AND estado = 'Pendiente'
                AND NOT EXISTS (
                    SELECT 1 FROM pedidos
                    WHERE factura_id = facturacion.id
                )
                """,
                (registro_id,)
            )

            eliminado = cursor.rowcount == 1

            conn.commit()

        except psycopg.Error:
            conn.rollback()

            app.logger.exception(
                "No se pudo eliminar el registro %s",
                registro_id
            )

            flash("No se pudo eliminar el registro.", "danger")

        else:
            if eliminado:
                flash("Registro eliminado correctamente.", "success")

            else:
                flash("El registro ya no se puede eliminar.", "warning")

        finally:
            conn.close()

        return redirect(url_for("facturacion"))

    return render_template(
        "eliminar_factura.html",
        registro=registro,
        form=form
    )


# COMPROBANTES

@app.route("/admin/facturacion/<int:registro_id>/comprobante")
@login_required
@acceso_requerido
def comprobante(registro_id):
    registro = consultar(
        """
        SELECT
            f.id, c.nombre, c.correo, c.telefono,
            p.nombre, f.cantidad, f.precio_unitario,
            f.total, f.fecha, f.metodo_pago,
            f.referencia, f.estado, f.fecha_pago
        FROM facturacion AS f
        JOIN clientes AS c ON c.id = f.cliente_id
        JOIN productos AS p ON p.id = f.producto_id
        WHERE f.id = %s
        """,
        (registro_id,),
        uno=True
    )

    if registro is None:
        abort(404)

    if registro[11] != "Pagado":
        flash(
            "Confirma el pago antes de emitir el comprobante.",
            "warning"
        )

        return redirect(url_for("facturacion"))

    return render_template(
        "comprobante.html",
        registro=registro
    )


@app.route("/cliente/pedidos/<int:pedido_id>/comprobante")
@login_required
@cliente_requerido
def comprobante_cliente(pedido_id):
    cliente = obtener_cliente_actual()

    registro = consultar(
        """
        SELECT
            f.id, c.nombre, c.correo, c.telefono,
            p.servicio, f.cantidad, f.precio_unitario,
            f.total, f.fecha, f.metodo_pago,
            f.referencia, f.estado, f.fecha_pago
        FROM pedidos AS p
        JOIN facturacion AS f ON f.id = p.factura_id
        JOIN clientes AS c ON c.id = p.cliente_id
        WHERE p.id = %s
        AND p.cliente_id = %s
        AND f.cliente_id = %s
        """,
        (pedido_id, cliente[0], cliente[0]),
        uno=True
    )

    if registro is None:
        abort(404)

    if registro[11] != "Pagado":
        flash(
            "El comprobante estará disponible cuando "
            "la administración confirme tu pago.",
            "info"
        )

        return redirect(url_for("mis_pedidos"))

    return render_template(
        "comprobante.html",
        registro=registro,
        es_cliente=True
    )


# ADMINISTRACIÓN DE PEDIDOS

def consultar_pedido(pedido_id, cliente_id=None):
    conn = conectar()
    conn.row_factory = dict_row

    try:
        sql = """
            SELECT
                p.*,
                c.nombre AS cliente,
                c.correo,
                c.telefono,
                f.cantidad,
                f.total,
                f.estado AS estado_pago
            FROM pedidos AS p
            JOIN clientes AS c ON c.id = p.cliente_id
            JOIN facturacion AS f ON f.id = p.factura_id
            WHERE p.id = %s
            AND f.cliente_id = p.cliente_id
        """

        parametros = [pedido_id]

        if cliente_id is not None:
            sql += " AND p.cliente_id = %s"
            parametros.append(cliente_id)

        return conn.execute(sql, parametros).fetchone()

    finally:
        conn.close()


@app.route("/admin/pedidos")
@login_required
@acceso_requerido
def pedidos_admin():
    conn = conectar()
    conn.row_factory = dict_row

    try:
        pedidos = conn.execute(
            """
            SELECT
                p.id,
                c.nombre AS cliente,
                p.servicio,
                f.estado AS estado_pago,
                p.estado_trabajo,
                p.fecha
            FROM pedidos AS p
            JOIN clientes AS c ON c.id = p.cliente_id
            JOIN facturacion AS f ON f.id = p.factura_id
            WHERE f.cliente_id = p.cliente_id
            ORDER BY p.id DESC
            """
        ).fetchall()

    finally:
        conn.close()

    return render_template(
        "pedidos_admin.html",
        pedidos=pedidos
    )


@app.route(
    "/admin/pedidos/<int:pedido_id>",
    methods=["GET", "POST"]
)
@login_required
@acceso_requerido
def gestionar_pedido(pedido_id):
    pedido = consultar_pedido(pedido_id)

    if pedido is None:
        abort(404)

    form = GestionPedidoForm()

    if request.method == "GET":
        form.estado_trabajo.data = pedido["estado_trabajo"]
        form.observaciones.data = pedido["observaciones"]

    if form.validate_on_submit():
        archivo = form.archivo.data
        tiene_archivo = bool(archivo and archivo.filename)

        contenido = None
        nombre_original = ""

        if tiene_archivo:
            nombre_original = secure_filename(archivo.filename)
            extension = nombre_original.rsplit(".", 1)[-1].lower()

            permitidas = {
                "pdf", "docx", "xlsx", "pptx",
                "txt", "png", "jpg", "jpeg"
            }

            if not nombre_original or extension not in permitidas:
                form.archivo.errors.append(
                    "Selecciona un archivo permitido."
                )

            else:
                contenido = archivo.stream.read(MAX_ARCHIVO + 1)

                if not contenido or len(contenido) > MAX_ARCHIVO:
                    form.archivo.errors.append(
                        "El archivo debe tener contenido "
                        "y pesar como máximo 10 MB."
                    )

        if not form.archivo.errors:
            conn = conectar()
            conn.row_factory = dict_row

            try:
                actual = conn.execute(
                    """
                    SELECT archivo_guardado, archivo_contenido
                    FROM pedidos
                    WHERE id = %s
                    FOR UPDATE
                    """,
                    (pedido_id,)
                ).fetchone()

                if actual is None:
                    abort(404)

                if (
                    form.estado_trabajo.data == "Entregado"
                    and not (
                        contenido or actual["archivo_contenido"]
                    )
                ):
                    form.archivo.errors.append(
                        "Adjunta el resultado antes de marcar "
                        "el pedido como entregado."
                    )

                    conn.rollback()

                else:
                    conn.execute(
                        """
                        UPDATE pedidos
                        SET estado_trabajo = %s, observaciones = %s
                        WHERE id = %s
                        """,
                        (
                            form.estado_trabajo.data,
                            form.observaciones.data or "",
                            pedido_id
                        )
                    )

                    if contenido is not None:
                        conn.execute(
                            """
                            UPDATE pedidos
                            SET archivo_contenido = %s,
                                archivo_original = %s,
                                archivo_guardado = %s
                            WHERE id = %s
                            """,
                            (
                                contenido,
                                nombre_original,
                                secrets.token_hex(24),
                                pedido_id
                            )
                        )

                    conn.commit()

                    flash("Pedido actualizado correctamente.", "success")

                    return redirect(
                        url_for(
                            "gestionar_pedido",
                            pedido_id=pedido_id
                        )
                    )

            except psycopg.Error:
                conn.rollback()

                app.logger.exception(
                    "No se pudo actualizar el pedido %s",
                    pedido_id
                )

                flash(
                    "No se guardó la actualización. Intenta nuevamente.",
                    "danger"
                )

            finally:
                conn.close()

    return render_template(
        "gestionar_pedido.html",
        pedido=pedido,
        form=form
    )


# DESCARGA DE RESULTADOS

def enviar_archivo(pedido):
    nombre = pedido["archivo_original"] or "resultado"

    tipo = (
        mimetypes.guess_type(nombre)[0]
        or "application/octet-stream"
    )

    respuesta = send_file(
        BytesIO(bytes(pedido["archivo_contenido"])),
        mimetype=tipo,
        as_attachment=True,
        download_name=nombre,
        max_age=0
    )

    respuesta.headers["Cache-Control"] = "private, no-store"
    respuesta.headers["X-Content-Type-Options"] = "nosniff"

    return respuesta


@app.route("/cliente/pedidos/<int:pedido_id>/descargar")
@login_required
@cliente_requerido
def descargar_entrega(pedido_id):
    cliente = obtener_cliente_actual()

    pedido = consultar_pedido(pedido_id, cliente[0])

    if pedido is None:
        abort(404)

    if (
        pedido["estado_pago"] != "Pagado"
        or pedido["estado_trabajo"] != "Entregado"
        or not pedido["archivo_contenido"]
    ):
        flash(
            "La descarga estará disponible cuando "
            "el pedido esté pagado y entregado.",
            "info"
        )

        return redirect(url_for("mis_pedidos"))

    return enviar_archivo(pedido)


@app.route("/admin/pedidos/<int:pedido_id>/descargar")
@login_required
@acceso_requerido
def descargar_entrega_admin(pedido_id):
    pedido = consultar_pedido(pedido_id)

    if pedido is None or not pedido["archivo_contenido"]:
        abort(404)

    return enviar_archivo(pedido)


@app.errorhandler(413)
def archivo_demasiado_grande(error):
    return (
        "El archivo supera el límite permitido. "
        "Vuelve atrás y selecciona un archivo de hasta 10 MB.",
        413
    )


# INICIAR LA APLICACIÓN

crear_base_datos()
preparar_administrador()

if __name__ == "__main__":
    if "--crear-admin" in sys.argv:
        crear_administrador()

    else:
        app.run(
            debug=os.environ.get("FLASK_DEBUG") == "1"
        )