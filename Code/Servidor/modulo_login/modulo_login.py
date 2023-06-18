from flask import flash, render_template
from flask import request
from flask_login import LoginManager, login_required, login_user, logout_user, current_user
from wtforms import ValidationError
import os
from modulo_bbdd.modulo_bbdd import *
from modulo_forms.modulo_forms import *
from modulo_funcionesAux.modulo_funcionesAux import *

modulo_login = Blueprint("modulo_login", __name__, static_folder="static", template_folder="templates")

login_manager = LoginManager()
login_manager.init_app(current_app)
login_manager.login_view = 'login'

user_id_actual = None


@login_manager.user_loader
def load_user(user_id):
    '''
    Descripción: Método que permite recoger el usuario de la base de datos 
    Parámetros de entrada: id del usuario loggeado
    Returns: Recoge el usuario correspondiente 
    '''
    return User.query.get(int(user_id))


@login_manager.unauthorized_handler
def unauthorized_callback():
    '''
    Descripción: Método que comprueba que la página a la que es redirigido el usuario es válida (es válida si el usuario está loggeado)
    Parámetros de entrada: ninguno
    Returns: redirige a la página correspondiente si es válida
    '''
    return redirect('/login?nextpath=' + request.full_path.replace("&", "___and___"))


def validate_username(self, username):
    '''
    Descripción: Método que valida que el nombre del usuario introducido al loggearse es válido
    Parámetros de entrada: nombre del usuario a comprobar formato XXXX
    Returns: devuelve true si es válido o lanza un error de lo contrario
    '''
    user = User.query.filter_by(username=username.data).first()
    if user is not None:
        raise ValidationError('Please use a different username.')
    return True


def validate_email(self, email):
    '''
    Descripción: Método que permite comprobar que el email del usuario es válido
    Parámetros de entrada: email a comprobar formato XXXX@XXXX.XXXX
    Returns: devuelve true si es válido o lanza un error de lo contrario
    '''
    user = User.query.filter_by(email=email.data).first()
    if user is not None:
        raise ValidationError('Please use a different email address.')
    return True


@modulo_login.route('/login', methods=['GET', 'POST'])
def login():
    '''
    Descripción: Función que permite devolver la página de login si se accede por GET o permite loggear al usuario si se recibe por POST
    Parámetros de entrada: Ninguno
    Returns: Renderiza el template de login.html por GET o redirecciona a la página desde donde se pidió el login por POST
    '''
    global user_id_actual
    form = LoginForm()
    if request.method == 'POST':
        if form.validate_on_submit():
            user = User.query.filter(
                (User.email == form.username_or_email.data) | (User.username == form.username_or_email.data)).first()
            if user is None or not user.check_password(form.password.data):
                flash('Invalid username or password')
                return redirect(url_for('modulo_login.login'))

            login_user(user)
            next_page = request.form.get('nextpath')

            print("El next_page en el POST es {}".format(next_page))

            if next_page == "None":
                print("next_page es None")
                next_page = url_for("modulo_modelos.modelos")

            set_authenticated(True)
            return redirect(next_page)
    else:
        next_page = request.args.get('nextpath')
        print("El next_page en el GET es {}".format(next_page))
        return render_template('login.html', form=form, module="login", nextpath=next_page)


RUTA = "/../users_models/" ## Ruta base del fichero que almacena todos los usuarios y sus proyectos


def crear_carpeta_usuario(usuario):
    '''
    Descripción: Función que permite crear la carpeta para los proyectos del usuario en la web
    Parámetros de entrada: el usuario del que se quiere crear la carpeta
    Returns: Nada
    '''
    current_directory = os.path.dirname(os.path.abspath(__file__))
    ruta_final = current_directory + RUTA + str(usuario.id)
    os.mkdir(ruta_final)
    return


@modulo_login.route('/signup', methods=['GET', 'POST'])
def signup():
    '''
    Descripción: Función que permite registrar un usuario en la base de datos
    Parámetros de entrada: ninguno
    Returns: redirecciona a la página de login con un método GET
    '''
    form = SignUpForm()
    if request.method == 'POST':
        if form.validate_on_submit():
            nuevoUser = User(
                username=form.username.data,
                email=form.email.data,
            )
            user = User.query.filter((User.email == nuevoUser.email) | (User.username == nuevoUser.username)).first()
            if user is not None:
                flash('Ya existe una cuenta con ese correo o nombre de usuario')
                return render_template("signup.html", form=form, module="signup")
            nuevoUser.set_password(form.password.data)
            print("Usuario registrado con éxito")
            flash('Usuario creado con éxito!')
            db.session.add(nuevoUser)
            db.session.commit()
            crear_carpeta_usuario(nuevoUser)
            return redirect(url_for('modulo_login.login'))
    else:
        print("El formulario no es válido")
    return render_template("signup.html", form=form, module="signup")


@modulo_login.route('/logout', methods=['GET'])
@login_required
def logout():
    '''
    Descripción: Función que permite abandonar la sesión actual del usuario en la plataforma
    Parámetros de entrada: ninguno
    Returns: dirección a la página principal pre-login
    '''
    logout_user()
    set_authenticated(False)
    return redirect(url_for('index'))


def getCurrentUserEmailLogin():
    '''
    Descripción: Función que permite obtener el email del usuario
    Parámetros de entrada: ninguno
    Returns: email del usuario asociada al usuario de la sesión actual
    '''
    user_email = User.query.filter(User.id == current_user.id).first().email
    return user_email
