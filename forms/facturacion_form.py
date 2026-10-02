from flask_wtf import FlaskForm
from wtforms import StringField, DecimalField, SubmitField
from wtforms.validators import DataRequired, NumberRange


class FacturacionForm(FlaskForm):
    cliente = StringField(
        'Cliente',
        validators=[DataRequired()]
    )

    servicio = StringField(
        'Servicio',
        validators=[DataRequired()]
    )

    total = DecimalField(
        'Total',
        validators=[DataRequired(), NumberRange(min=0)]
    )

    submit = SubmitField('Registrar factura')
