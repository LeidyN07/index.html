# TecnoAyuda

Proyecto integrador de Desarrollo de Aplicaciones Web.

**Autora:** Leidy  
**Universidad:** Universidad Estatal Amazónica  
**Año:** 2026

## Descripción

TecnoAyuda es un sistema web de apoyo académico y digital.
Permite consultar servicios, registrar una cuenta de cliente,
solicitar servicios y revisar el avance de los pedidos.

La administradora gestiona clientes, servicios, colaboradores,
pedidos y registros de facturación. También puede confirmar
pagos y adjuntar los resultados de los trabajos.

## Tecnologías

- Python
- Flask
- Flask-WTF y WTForms
- SQLite
- HTML, CSS y JavaScript
- Bootstrap 5.3.3

## Funcionalidades

- Autenticación de administradora y clientes.
- Catálogo de servicios.
- CRUD de clientes, servicios y facturación.
- Registro y seguimiento de pedidos.
- Actualización del estado del trabajo.
- Entrega y descarga de archivos.
- Comprobantes internos de pagos confirmados.
- Formulario público de solicitudes de orientación.

Los archivos entregados solo pueden descargarse por el cliente
propietario del pedido cuando esté pagado y entregado.

La confirmación del pago es manual. El sistema no procesa
pagos bancarios ni pagos con tarjeta.

## Estructura principal

- `app.py`: configuración, rutas y operaciones de base de datos.
- `requirements.txt`: dependencias de Python.
- `forms/`: formularios y validaciones.
- `templates/`: páginas HTML de Flask.
- `static/css/`: estilos.
- `static/js/`: JavaScript.
- `static/img/`: imágenes locales.
- `data/tecnoayuda.db`: base de datos local.
- `data/entregas/`: archivos privados de los trabajos.

La base de datos y la carpeta de entregas se crean
automáticamente al ejecutar la aplicación.

## Instalación y ejecución

1. Descargar o clonar el repositorio.
2. Abrir la carpeta principal del proyecto en Visual Studio Code.
3. Abrir una terminal dentro de esa carpeta.
4. Crear un entorno virtual:

```bash
python -m venv .venv
```

5. En Windows PowerShell, activar el entorno:

```powershell
.\.venv\Scripts\Activate.ps1
```

Si PowerShell no permite activarlo, se puede utilizar directamente
el Python del entorno para instalar y ejecutar:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe app.py --crear-admin
.\.venv\Scripts\python.exe app.py
```

6. Con el entorno activado, instalar las dependencias:

```bash
python -m pip install -r requirements.txt
```

7. Crear la cuenta de administración:

```bash
python app.py --crear-admin
```

Elegir un usuario y una contraseña de al menos 12 caracteres.
Al escribir la contraseña en la terminal, los caracteres
no se muestran. Si ya existe una cuenta de administración,
el sistema lo indicará.

8. Iniciar el servidor:

```bash
python app.py
```

9. Abrir en el navegador:

```text
http://127.0.0.1:5000
```

Mantener la terminal abierta mientras se utiliza el sistema.
Para detenerlo, presionar `Ctrl + C`.

## Acceso al sistema

- Los clientes pueden crear su cuenta desde “Crear cuenta”.
- La administradora accede desde “Administración”.
- Las credenciales se eligen localmente; no se publican
  contraseñas en el repositorio.
- Al reiniciar el servidor, puede ser necesario iniciar sesión
  nuevamente porque la clave de sesión se genera en cada ejecución.

## Tablas relacionadas

El sistema incluye, entre otras, estas tres tablas:

- `clientes`: datos de contacto.
- `productos`: servicios y precios.
- `facturacion`: relaciona un cliente con un servicio mediante
  `cliente_id` y `producto_id`.

La tabla `pedidos` también se relaciona con clientes,
servicios y facturación.

## Pruebas del CRUD

Utilizar datos de prueba para la demostración:

1. Crear un cliente de prueba y consultar su registro.
2. Editar sus datos.
3. Crear un servicio de prueba y consultar su registro.
4. Editar su descripción o precio.
5. Crear un registro de facturación pendiente que relacione
   ese cliente y ese servicio, sin marcar el pago como recibido.
6. Editar la cantidad y comprobar el total.
7. Eliminar ese registro de facturación.
8. Eliminar el servicio y el cliente de prueba.

Este orden permite demostrar las relaciones entre las tres tablas.

El sistema impide eliminar clientes o servicios con registros
relacionados. Los registros de facturación pagados o vinculados
a pedidos no se pueden editar ni eliminar desde el CRUD.

## Prueba del recorrido del cliente

1. Crear una cuenta de cliente.
2. Elegir un servicio del catálogo y confirmar el pedido.
3. Como administradora, revisar y actualizar el pedido.
4. Confirmar el pago recibido o usar un pago simulado
   identificado como prueba durante la demostración.
5. Adjuntar un archivo de resultado y marcar el pedido
   como “Entregado”.
6. Como cliente, entrar en “Mis pedidos”.
7. Descargar el resultado y consultar el comprobante.
8. Probar “Imprimir / Guardar PDF”.

También se debe comprobar que una persona sin sesión no pueda
entrar en las rutas privadas y que un cliente no pueda descargar
los archivos de otro cliente.

## Consideraciones

- Los comprobantes son documentos internos del proyecto académico;
  no constituyen facturas tributarias.
- Los archivos adjuntos tienen un límite de 10 MB.
- El correo y teléfono de la página principal son datos de ejemplo.
- Bootstrap y la imagen externa requieren conexión a internet.
- El modo de depuración se utiliza para la demostración local.
- GitHub almacena el código del proyecto. GitHub Pages no ejecuta
  Flask ni SQLite; para probar estas funciones se debe ejecutar
  la aplicación con Python.