from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, IntegerField, FloatField, SelectField
from wtforms.validators import (
    DataRequired, InputRequired, Email, Length, EqualTo, NumberRange, ValidationError,
)
from app.models import Usuario


class LoginForm(FlaskForm):
    email = StringField("Correo", validators=[DataRequired(), Email()])
    password = PasswordField("Contraseña", validators=[DataRequired()])
    submit = SubmitField("Ingresar")


class RegisterForm(FlaskForm):
    nombre = StringField("Nombre", validators=[DataRequired(), Length(max=80)])
    email = StringField("Correo", validators=[DataRequired(), Email(), Length(max=120)])
    password = PasswordField("Contraseña", validators=[DataRequired(), Length(min=6)])
    confirm = PasswordField(
        "Repetir contraseña",
        validators=[DataRequired(), EqualTo("password", message="Las contraseñas no coinciden")],
    )
    submit = SubmitField("Crear cuenta")

    def validate_email(self, field):
        if Usuario.query.filter_by(email=field.data.lower()).first():
            raise ValidationError("Ese correo ya está registrado.")
class ProductoForm(FlaskForm):
    sku = StringField("SKU / Código", validators=[DataRequired(), Length(max=40)])
    nombre = StringField("Nombre", validators=[DataRequired(), Length(max=120)])
    precio = FloatField("Precio (CLP)", validators=[InputRequired(), NumberRange(min=0)])
    stock_actual = IntegerField(
        "Stock inicial", default=0, validators=[InputRequired(), NumberRange(min=0)]
    )
    stock_minimo = IntegerField(
        "Stock mínimo (alerta)", default=5, validators=[InputRequired(), NumberRange(min=0)]
    )
    categoria_id = SelectField("Categoría", coerce=int)
    proveedor_id = SelectField("Proveedor", coerce=int)
    submit = SubmitField("Guardar")