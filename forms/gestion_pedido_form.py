from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import SelectField, TextAreaField, SubmitField
from wtforms.validators import InputRequired, Optional, Length


class GestionPedidoForm(FlaskForm):

    estado_trabajo = SelectField(
        'Estado del trabajo',
        choices=[
            ('Recibido', 'Recibido'),
            ('En proceso', 'En proceso'),
            ('Entregado', 'Entregado')
        ],
        validators=[
            InputRequired(message='Selecciona el estado del trabajo.')
        ]
    )

    observaciones = TextAreaField(
        'Mensaje para el cliente',
        filters=[lambda valor: valor.strip() if valor else valor],
        validators=[
            Optional(),
            Length(
                max=1000,
                message='El mensaje no debe superar los 1000 caracteres.'
            )
        ]
    )

    archivo = FileField(
        'Archivo del trabajo terminado',
        validators=[
            FileAllowed(
                ['pdf', 'docx', 'xlsx', 'pptx', 'txt', 'png', 'jpg', 'jpeg'],
                message='Selecciona un PDF, documento, presentación, '
                        'hoja de cálculo, texto o imagen.'
            )
        ]
    )

    submit = SubmitField('Guardar actualización')