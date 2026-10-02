from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, Email, Length


class ClienteForm(FlaskForm):
    nombre = StringField(
        'Nombre',
        validators=[DataRequired(), Length(min=3, max=100)]
    )

    correo = StringField(
        'Correo electrónico',
        validators=[DataRequired(), Email()]
    )

    telefono = StringField(
        'Teléfono',
        validators=[DataRequired(), Length(min=7, max=15)]
    )

    submit = SubmitField('Guardar cliente')
