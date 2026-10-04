from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import (
    DataRequired,
    Length,
    Regexp,
    EqualTo
)


def limpiar_texto(valor):
    return valor.strip() if valor else valor


def limpiar_correo(valor):
    return valor.strip().lower() if valor else valor


class RegistroClienteForm(FlaskForm):

    nombre = StringField(
        'Nombre completo',
        filters=[limpiar_texto],
        validators=[
            DataRequired(message='Escribe tu nombre.'),
            Length(
                min=3,
                max=100,
                message='El nombre debe tener entre 3 y 100 caracteres.'
            )
        ]
    )

    correo = StringField(
        'Correo electrónico',
        filters=[limpiar_correo],
        validators=[
            DataRequired(message='Escribe tu correo electrónico.'),
            Length(
                max=150,
                message='El correo no debe superar los 150 caracteres.'
            ),
            Regexp(
                r'^[^\s@]+@[^\s@]+\.[^\s@]+$',
                message='Escribe un correo válido.'
            )
        ]
    )

    telefono = StringField(
        'Teléfono',
        filters=[limpiar_texto],
        validators=[
            DataRequired(message='Escribe tu teléfono.'),
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

    clave = PasswordField(
        'Contraseña',
        validators=[
            DataRequired(message='Escribe una contraseña.'),
            Length(
                min=12,
                max=128,
                message='La contraseña debe tener entre 12 y 128 caracteres.'
            )
        ]
    )

    confirmar_clave = PasswordField(
        'Repite la contraseña',
        validators=[
            DataRequired(message='Repite tu contraseña.'),
            EqualTo(
                'clave',
                message='Las contraseñas no coinciden.'
            )
        ]
    )

    submit = SubmitField('Crear mi cuenta')


class LoginClienteForm(FlaskForm):

    correo = StringField(
        'Correo electrónico',
        filters=[limpiar_correo],
        validators=[
            DataRequired(message='Escribe tu correo electrónico.'),
            Length(
                max=150,
                message='El correo no debe superar los 150 caracteres.'
            )
        ]
    )

    clave = PasswordField(
        'Contraseña',
        validators=[
            DataRequired(message='Escribe tu contraseña.'),
            Length(
                max=128,
                message='La contraseña no debe superar los 128 caracteres.'
            )
        ]
    )

    submit = SubmitField('Ingresar a mi cuenta')