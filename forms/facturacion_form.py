from flask_wtf import FlaskForm
from wtforms import (
    SelectField,
    IntegerField,
    StringField,
    BooleanField,
    SubmitField
)
from wtforms.validators import (
    InputRequired,
    NumberRange,
    Length,
    Optional
)


class FacturacionForm(FlaskForm):

    cliente_id = SelectField(
        'Cliente',
        coerce=int,
        choices=[],
        validators=[
            InputRequired(message='Selecciona un cliente.')
        ],
        validate_choice=True
    )

    producto_id = SelectField(
        'Servicio',
        coerce=int,
        choices=[],
        validators=[
            InputRequired(message='Selecciona un servicio.')
        ],
        validate_choice=True
    )

    cantidad = IntegerField(
        'Cantidad',
        default=1,
        validators=[
            InputRequired(message='Ingresa la cantidad.'),
            NumberRange(
                min=1,
                max=1000,
                message='La cantidad debe estar entre 1 y 1000.'
            )
        ]
    )

    metodo_pago = SelectField(
        'Método de pago',
        choices=[
            ('', 'Selecciona un método'),
            ('Efectivo', 'Efectivo'),
            ('Transferencia', 'Transferencia bancaria')
        ],
        validators=[
            InputRequired(message='Selecciona el método de pago.')
        ],
        validate_choice=True
    )

    referencia = StringField(
        'Referencia de la transferencia (opcional)',
        filters=[lambda valor: valor.strip() if valor else valor],
        validators=[
            Optional(),
            Length(
                max=100,
                message='La referencia no debe superar los 100 caracteres.'
            )
        ]
    )

    pagado = BooleanField(
        'Confirmo que recibí el pago completo'
    )

    submit = SubmitField('Guardar registro')