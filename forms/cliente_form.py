from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, Length, Regexp


def limpiar_texto(valor):
    return valor.strip() if valor else valor


class ClienteForm(FlaskForm):

    nombre = StringField(
        'Nombre completo',
        filters=[limpiar_texto],
        validators=[
            DataRequired(message='Escribe el nombre del cliente.'),
            Length(
                min=3,
                max=100,
                message='El nombre debe tener entre 3 y 100 caracteres.'
            )
        ]
    )

    correo = StringField(
        'Correo electrónico',
        filters=[limpiar_texto],
        validators=[
            DataRequired(message='Escribe el correo electrónico.'),
            Length(
                max=150,
                message='El correo no debe superar los 150 caracteres.'
            ),
            Regexp(
                r'^[^\s@]+@[^\s@]+\.[^\s@]+$',
                message='Escribe un correo válido, como nombre@ejemplo.com.'
            )
        ]
    )

    telefono = StringField(
        'Teléfono',
        filters=[limpiar_texto],
        validators=[
            DataRequired(message='Escribe el teléfono del cliente.'),
            Length(
                min=7,
                max=20,
                message='El teléfono debe tener entre 7 y 20 caracteres.'
            ),
            Regexp(
                r'^\+?[0-9][0-9 ()-]*$',
                message='Usa números, espacios, paréntesis o guiones.'
            )
        ]
    )

    submit = SubmitField('Guardar cliente')