from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    TextAreaField,
    SelectField,
    SubmitField
)
from wtforms.validators import DataRequired, Length


class SolicitudForm(FlaskForm):

    nombre = StringField(
        'Nombre',
        filters=[lambda valor: valor.strip() if valor else valor],
        validators=[
            DataRequired(message='Escribe tu nombre.'),
            Length(
                min=3,
                max=100,
                message='El nombre debe tener entre 3 y 100 caracteres.'
            )
        ]
    )

    descripcion = TextAreaField(
        '¿En qué necesitas apoyo?',
        filters=[lambda valor: valor.strip() if valor else valor],
        validators=[
            DataRequired(message='Describe la ayuda que necesitas.'),
            Length(
                min=5,
                max=300,
                message='La descripción debe tener entre 5 y 300 caracteres.'
            )
        ]
    )

    categoria = SelectField(
        'Categoría',
        choices=[
            ('', 'Selecciona una categoría'),
            ('Correo electrónico', 'Correo electrónico'),
            ('Documentos y tareas', 'Documentos y tareas'),
            ('Soporte técnico', 'Soporte técnico')
        ],
        validators=[
            DataRequired(message='Selecciona una categoría.')
        ]
    )

    submit = SubmitField('Enviar solicitud')