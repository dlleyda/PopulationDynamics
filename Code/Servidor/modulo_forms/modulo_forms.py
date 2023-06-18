from flask import Blueprint
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import EqualTo, DataRequired

modulo_forms = Blueprint("modulo_forms", __name__, static_folder="static", template_folder="templates")


class LoginForm(FlaskForm):
    '''
    Formulario de login.
    '''
    username_or_email = StringField('Nombre de Usuario', validators=[DataRequired()])
    password = PasswordField('Contraseña', id='password')
    show_password = BooleanField('Mostrar Contraseña', id='check')
    submit = SubmitField('Log in')


class SignUpForm(FlaskForm):
    '''
    Formulario de registro.
    '''
    username = StringField('Nombre de Usuario', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired()])
    password = PasswordField('Contraseña', validators=[DataRequired()])
    confirm_password = PasswordField(
        'Repetir Contraseña', validators=[DataRequired(), EqualTo('password')])
    user_agreement = BooleanField('Acepto todos los acuerdos de licencia de usuario')
    submit = SubmitField('Sign up')


class CrearModeloForm(FlaskForm):
    '''
    Formulario para crear un nuevo modelo.
    '''
    nombre = StringField('Nombre', validators=[DataRequired()])
    publico = BooleanField('Hacer Público el Modelo')
    submit = SubmitField('Crear')


class AnadirModeloForm(FlaskForm):
    '''
    Formulario para añadir un modelo compartido.
    '''
    codigo = StringField('Código', validators=[DataRequired()])
    submit = SubmitField('Añadir')


@modulo_forms.route('/modulo_forms/test')
def modulo_forms_test():
    return 'OK'
