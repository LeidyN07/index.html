from flask_wtf import FlaskForm
from wtforms import StringField, DecimalField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Length, NumberRange


class ProductoForm(FlaskForm):
    nombre = StringField(
        'Nombre del servicio',
        validators=[DataRequired(), Length(min=3, max=100)]
    )

    descripcion = TextAreaField(
        'Descripción',
        validators=[DataRequired(), Length(min=5, max=300)]
    )

    precio = DecimalField(
        'Precio',
        validators=[DataRequired(), NumberRange(min=0)]
    )

    submit = SubmitField('Guardar servicio')
