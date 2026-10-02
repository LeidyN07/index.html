from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, Length


class ProveedorForm(FlaskForm):
    nombre = StringField(
        'Nombre',
        validators=[DataRequired(), Length(min=3, max=100)]
    )

    contacto = StringField(
        'Contacto',
        validators=[DataRequired()]
    )

    servicio = StringField(
        'Servicio que ofrece',
        validators=[DataRequired()]
    )

    submit = SubmitField('Guardar proveedor')
