from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError
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