from flask import Blueprint, current_app, url_for, redirect, make_response
from flask_login import current_user

modulo_funcionesAux = Blueprint("modulo_funcionesAux", __name__, static_folder="static", template_folder="templates")

ALLOWED_EXTENSIONS = {'xlsx'}
is_authenticated = False
current_tab = "modelos"


def set_authenticated(value=True):
    '''
    Descripción: Método que establece al usuario como autenticado o no
    Parámetros de entrada: booleano 
    Returns: Nada
    '''
    global is_authenticated
    is_authenticated = value


def get_authenticated():
    '''
    Descripción: Método que devuelve el estado de autenticación del usuario
    Parámetros de entrada: Ninguno
    Returns: valor del estado de autenticación del usuario (Bool)
    '''
    global is_authenticated
    
    return is_authenticated


def set_current_tab(tab):
    '''
    Descripción: Método que settea en qué sección está el usuario
    Parámetros de entrada: Sección donde se encuentra (String)
    Returns: Nada
    '''
    global current_tab
    current_tab = tab


def get_current_tab():
    '''
    Descripción: Método que devuelve la sección donde se encuentra el usuario
    Parámetros de entrada: Ninguno
    Returns: Sección donde se encuentra el usuario (String)
    '''
    global current_tab
    return current_tab


def allowed_file(filename):
    '''
    Descripción: Método que evalúa si el tipo de fichero introducido es válido
    Parámetros de entrada: nombre del fichero (String)
    Returns: Estado de validez (Bool)
    '''
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def get_extension(filename):
    '''
    Descripción: Método que permite la recoger la extensión de un fichero
    Parámetros de entrada: nombre del fichero (String)
    Returns: extensión del fichero (String)
    '''
    return filename.rsplit('.', 1)[1].lower()


def llamada_login_con_nextpath(nexpath):
    '''
    Descripción: Método que permite loggearse y que la web le rediriga a la página que ha intentado acceder mientras no estaba loggeado
    Parámetros de entrada: ruta a la que se quiere redirigir (String)
    Returns: Respuesta de la redirección (Object-Response)
    '''
    if not current_user.is_authenticated:
        response = make_response(redirect(url_for('modulo_login.login',
                                                  nextpath=nexpath)))
        return response


def generarEnlace(id):
    '''
    Descripción: Método que permite generar enlaces basado en el id 
    Parámetros de entrada: id del usuario (Integer)
    Returns: ruta con el enlace (String)
    '''
    return "localhost:5000/nuevoProyecto?project_id=" + str(id)


@current_app.context_processor
def utility_processor():
    '''
    Descripción: Método que permite acceder al contexto de la aplicación, permitiendo llamadas a funciones desde un template de jinja
    Parámetros de entrada: ninguno
    Returns: Diccionario con las funciones que se pueden ejecutar desde el template de Jinja (Dict)
    '''
    def get_authenticated():
        global is_authenticated
        return is_authenticated

    def get_current_tab():
        global current_tab
        return current_tab

    return dict(get_authenticated=get_authenticated, get_current_tab=get_current_tab)


