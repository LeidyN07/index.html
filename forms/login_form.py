from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Length


class LoginForm(FlaskForm):

    usuario = StringField(
        'Usuario',
        filters=[lambda valor: valor.strip() if valor else valor],
        validators=[
            DataRequired(message='Escribe tu usuario.'),
            Length(
                max=50,
                message='El usuario no debe superar los 50 caracteres.'
            )
        ]
    )

    clave = PasswordField(
        'Contraseña',
        validators=[
            DataRequired(message='Escribe tu contraseña.')
        ]
    )

    submit = SubmitField('Ingresar')