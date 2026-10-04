from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, Length


def limpiar_texto(valor):
    return valor.strip() if valor else valor


class ProveedorForm(FlaskForm):

    nombre = StringField(
        'Nombre del colaborador o negocio',
        filters=[limpiar_texto],
        validators=[
            DataRequired(message='Escribe el nombre del colaborador.'),
            Length(
                min=3,
                max=100,
                message='El nombre debe tener entre 3 y 100 caracteres.'
            )
        ]
    )

    contacto = StringField(
        'Correo o teléfono de contacto',
        filters=[limpiar_texto],
        validators=[
            DataRequired(message='Escribe un dato de contacto.'),
            Length(
                min=7,
                max=150,
                message='El contacto debe tener entre 7 y 150 caracteres.'
            )
        ]
    )

    servicio = StringField(
        'Servicio o apoyo que ofrece',
        filters=[limpiar_texto],
        validators=[
            DataRequired(message='Describe el apoyo que ofrece.'),
            Length(
                min=5,
                max=200,
                message='El servicio debe tener entre 5 y 200 caracteres.'
            )
        ]
    )

    submit = SubmitField('Guardar colaborador')