from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    DecimalField,
    TextAreaField,
    SubmitField
)
from wtforms.validators import (
    DataRequired,
    InputRequired,
    Length,
    NumberRange
)


class ProductoForm(FlaskForm):

    nombre = StringField(
        'Nombre del servicio',
        filters=[lambda valor: valor.strip() if valor else valor],
        validators=[
            DataRequired(message='Escribe el nombre del servicio.'),
            Length(
                min=3,
                max=100,
                message='El nombre debe tener entre 3 y 100 caracteres.'
            )
        ]
    )

    descripcion = TextAreaField(
        'Descripción',
        filters=[lambda valor: valor.strip() if valor else valor],
        validators=[
            DataRequired(message='Describe el servicio.'),
            Length(
                min=5,
                max=300,
                message='La descripción debe tener entre 5 y 300 caracteres.'
            )
        ]
    )

    precio = DecimalField(
        'Precio (USD)',
        places=2,
        validators=[
            InputRequired(message='Ingresa el precio del servicio.'),
            NumberRange(
                min=0,
                message='El precio debe ser cero o un valor positivo.'
            )
        ]
    )

    submit = SubmitField('Guardar servicio')
