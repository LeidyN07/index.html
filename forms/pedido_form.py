from flask_wtf import FlaskForm
from wtforms import TextAreaField, IntegerField, SubmitField
from wtforms.validators import (
    DataRequired,
    InputRequired,
    Length,
    NumberRange
)


class PedidoForm(FlaskForm):

    descripcion = TextAreaField(
        'Describe lo que necesitas',
        filters=[lambda valor: valor.strip() if valor else valor],
        validators=[
            DataRequired(message='Describe tu solicitud.'),
            Length(
                min=10,
                max=2000,
                message='La descripción debe tener entre 10 y 2000 caracteres.'
            )
        ]
    )

    cantidad = IntegerField(
        'Cantidad',
        default=1,
        validators=[
            InputRequired(message='Indica la cantidad.'),
            NumberRange(
                min=1,
                max=100,
                message='La cantidad debe estar entre 1 y 100.'
            )
        ]
    )

    submit = SubmitField('Confirmar pedido')