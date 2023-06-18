import json
import subprocess
import threading

from flask import Flask
from flask import jsonify
from flask_bootstrap import Bootstrap
from flask_cors import CORS, cross_origin

# Imports necesarios para calcular las ecuaciones teoricas para el modelo de poblaciones
import math
import numpy as np
from scipy.integrate import solve_ivp

# Iniciamos la app y distintas aplicaciones
app = Flask(__name__)
CORS(app)
bootstrap = Bootstrap(app)

# Configuramos la aplicacion con la base de datos
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///database/prueba.db"
app.config['SECRET_KEY'] = '37utopisdr jt ñçã3q0r9irjqwasdaADFSADF3q0r9irjqw'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Imports para registrar los modulos
with app.app_context():
    from modulo_funcionesAux.modulo_funcionesAux import *
    from modulo_bbdd.modulo_bbdd import *
    from modulo_login.modulo_login import *
    from modulo_forms.modulo_forms import *
    from modulo_modelos.modulo_modelos import *

app.register_blueprint(modulo_funcionesAux)
app.register_blueprint(modulo_forms)
app.register_blueprint(modulo_bbdd)
app.register_blueprint(modulo_login)
app.register_blueprint(modulo_modelos)


# Initialize the data of loktavolterra equations
x_init = (5, 5)
conejos = []
lobos = []

sol_lv = None
params = []
initial_state = True
ventana = 200
lim_theoretical_step = ventana


@app.route('/')
def index():
    return render_template("index.html")

datosMesa = {}

# Función que lee de un stdout los logs del modelo de entrenamiento
def lectura_datos_mesa(process, id):
    '''
    Funcion que almacena los logs del modelo de entrenamiento leídos a través de un stdout

    Params:
        -process::subprocess.Popen Subproceso creado para ejecutar el modelo
        -id::int Identificador del usuario para almacenar los datos para ese usuario
    '''

    global datosMesa

    while True:

        line = process.stdout.readline()

        if not line and process.poll() is not None:
            break

        linea_sucia = line.decode('latin-1')
        linea_limpia = linea_sucia.replace("\r\n", "").replace("\\\"", "\'")

        if "Interface starting at" in linea_limpia:
            continue
        if "WARNING" in linea_limpia:
            continue
        if not linea_limpia:
            continue

        ## Quitamos la última coma del último elemento para poder parsear el string a json con json.loads
        linea_limpia = linea_limpia[::-1].replace(",", "", 1)[::-1]

        # Insertar en la lista si no está vacía y si no existen datos meterlos
        try:
            datosMesa[id].append(json.loads(linea_limpia))
        except:
            datosMesa[id] = [json.loads(linea_limpia)]


@cross_origin()
@app.route("/crearModelo/<pretrained>", methods=['GET', 'POST'])
def crearModelo(pretrained):
    if request.method == 'POST':
        if (pretrained == "False"):
            pretrained = False
        else:
            pretrained = True

        '''
        Ruta que ejecuta el modelo de apredizaje por refuerzo a través de crear un subproceso y ejecutarlo en un thread

        Params:
            -pretrained::String Identificador booleano de si el usuario ha elegido un modelo preentrenado
        '''
        data = json.loads(request.data)
        modelo_id = data['modelo_id']
        user_id_actual = current_user.id

        final_directory = os.getcwd() + "\\users_models\\" + str(user_id_actual) + "\\proyecto" + str(modelo_id) + "\\"
        if (not pretrained):
            print(final_directory)
            with open(final_directory + "config.json", "w") as file:
                json.dump(data, file)
            print(data)

            command = ['python', '-u', '..\\Simulation\\simulation.py', final_directory]
        else:
            print(final_directory)
            command = ['python', '-u', '..\\Simulation\\simulation_open.py', final_directory]
        # """Run a command while printing the live output"""
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT
        )

        thread = threading.Thread(name='lectura_datos', target=lectura_datos_mesa, args=[process, "1"])

        thread.start()

        return "Entrenando modelo"

######################################################### RUTA PARA COMPROBAR QUE CIERTO USUARIO TIENE DATOS ##############################################################
# Ruta para ver datos nuevos del modelo
@cross_origin()
@app.route("/muestra/mesa/<id>")
def muestra_mesa(id):
    '''
    Ruta para debuggear y comprobar que hay datos nuevos

    Params:
        -id::int Identificador del usuario para almacenar los datos para ese usuario
    '''
    if id in datosMesa:
        datos_nuevos = datosMesa[id]
        datosMesa[id] = []
    else:
        datos_nuevos = []

    return jsonify(datos_nuevos)
############################################################################################################################################################################


def estimate(conejos, lobos):
    '''
    Algoritmo para hacer una estimación de parametros para las ecuaciones de lotka-volterra en base a los datos recogidos

    Params:
        -conjeos::list Lista de datos de número de conejos por cada iteración
        -lobos::list Lista de datos de número de lobos por cada iteración

    Errores posibles:
        - np.linalg.LinAlgError en el caso de que una matriz no sea invertible, se trata añadiendo a través de la distribución normal con media 0 ruido a las filas
    '''

    dif_conejos = [y - x for x, y in zip(conejos, conejos[1:])]
    dif_lobos = [y - x for x, y in zip(lobos, lobos[1:])]

    sum_conejos = [(y + x) / 2 for x, y in zip(conejos, conejos[1:])]
    sum_lobos = [(y + x) / 2 for x, y in zip(lobos, lobos[1:])]

    sum_mult = [(x_2 * y_2 + x_1 * y_1) / 2 for x_1, y_1, x_2, y_2 in zip(conejos, lobos, conejos[1:], lobos[1:])]

    X = np.matrix([sum_conejos, sum_mult])
    X_t = X
    X = X.transpose()

    Y = np.matrix([sum_lobos, sum_mult])
    Y_t = Y
    Y = Y.transpose()

    mult_Xt_X = np.matmul(X_t, X)
    try:
        inversa_Xt_X = np.linalg.inv(mult_Xt_X)
    except np.linalg.LinAlgError as err:
        
        vector_error = np.random.normal(loc=0, scale=0.001, size=(mult_Xt_X.shape))

        inversa_Xt_X = np.linalg.inv(mult_Xt_X + vector_error)

    tras_inv_conejos = np.matmul(inversa_Xt_X, X_t)
    A_conejos = np.matmul(tras_inv_conejos, np.array(dif_conejos))

    mult_Yt_Y = np.matmul(Y_t, Y)
    try:
        inversa_Yt_Y = np.linalg.inv(mult_Yt_Y)
    except np.linalg.LinAlgError as err:
        
        vector_error = np.random.normal(loc=0, scale=0.001, size=(mult_Yt_Y.shape))

        inversa_Yt_Y = np.linalg.inv(mult_Yt_Y + vector_error)

    tras_inv_lobos = np.matmul(inversa_Yt_Y, Y_t)
    A_lobos = np.matmul(tras_inv_lobos, np.array(dif_lobos))

    rl_practico = float(A_conejos[0][:, 0])
    alpha_practico = float(A_conejos[0][:, 1])
    beta_practico = float(A_lobos[0][:, 1])
    rz_practico = float(A_lobos[0][:, 0])

    return [rl_practico, alpha_practico, rz_practico, beta_practico]


def lotkavolterra_sobreescrito(t, x, rl, alpha, rz, beta):
    '''
    Función de lotka volterra

    Params:
        -t::float Necesario para resolver númericamente las ecuaciones diferenciales a través de solve_ivp
        -x::list Tupla donde el primer elemento tiene el número de liebres y el segundo el numero de lobos
        -rl::float Parametro que describe la tasa de crecimiento de las liebres
        -alpha::float Parametro que describe que por cada tantos zorros mueren alpha liebres
        -rz::float Parametro que describe la tasa de decrecimiento de los lobos
        -beta::float Parametro que describe que por cada tantas liebres crecen beta lobos

    Errores posibles:
        - np.linalg.LinAlgError en el caso de que una matriz no sea invertible, se trata añadiendo a través de la distribución normal con media 0, ruido a las filas
    '''
    return np.array([rl * x[0] + alpha * x[0] * x[1], rz * x[1] + beta * x[0] * x[1]])


# Funcion para actualizar datos de la funcion de lotka volterra teorica (dependientes del numero de especies que haya en un momento)
def data_loktavolterra(x_init, steps):
    '''
    Función que devuelve los datos de la resolución de las ecuaciones de lotka volterra

    Params:
        -x_init::tuple Tupla con el número inicial de lobos y liebres
        -steps::list Lista con todos los steps que ha hecho el modelo y por tanto los steps sobre los que queremos evaluar las ecuaciones de lotka-volterra

    Errores posibles:
        - forrtl: error (200): program aborting due to control-C event:
            Ocurre cuando se hace crtl+c cuando el servidor está arrancado, solución: https://stackoverflow.com/questions/15457786/ctrl-c-crashes-python-after-importing-scipy-stats
    '''

    # Linea para poder actualizar el valor de la variable global sol_lv
    global sol_lv
    global params

    t_span = (steps[0], steps[-1])
    t_eval = np.linspace(t_span[0], t_span[1], t_span[1] - t_span[0])

    sol_lv = solve_ivp(lotkavolterra_sobreescrito, t_span, x_init, args=tuple(params), t_eval=t_eval)


### Hay un error que salta al final de la ejecución cuando tiramos el servidor con crtl + c que scipy da un error, en esta url está la solución pero no sé si merece la pena
# forrtl: error (200): program aborting due to control-C event
# Image              PC                Routine            Line        Source
# libifcoremd.dll    00007FFE6FFA3B58  Unknown               Unknown  Unknown
# KERNELBASE.dll     00007FFF06F52603  Unknown               Unknown  Unknown
# KERNEL32.DLL       00007FFF08E37604  Unknown               Unknown  Unknown
# ntdll.dll          00007FFF092426A1  Unknown               Unknown  Unknown
###################### https://stackoverflow.com/questions/15457786/ctrl-c-crashes-python-after-importing-scipy-stats ##########################


# Funcion para recoger datos de la solucion numerica de lotka volterra dados unos steps
def get_loktavolterra_data(steps, contadores):
    '''
    Funcion para recoger datos de la solucion numerica de lotka volterra dados unos steps y devolver una lista con la estimación teórica de número de población (presa, depredador)

    Params:
        -steps::list Lista con todos los steps que ha hecho el modelo
        -contadores::list Lista de tuplas, donde por cada elemento representa la cantidad de (presas:conejos,depredador:lobo) por step
    '''
    global conejos
    global lobos
    global lim_theoretical_step
    global params
    global x_init
    global initial_state
    global sol_lv
    global ventana

    # Condiciones para almacenar o bien todos los datos o si no estamos en el estado inicial, actuar como una pila y mantener el número de datos sobre los que operamos
    if initial_state:
        for i in contadores:
            conejos.append(i[0])
            lobos.append(i[1])
        params = estimate(conejos, lobos)

        data_loktavolterra(x_init, steps)
    # Contadores para contar el numero de animales por cada especie
    else:
        for i in contadores:
            conejos.append(i[0])
            conejos.pop(0)
            lobos.append(i[1])
            lobos.pop(0)

    contadores_teoricos = []

    # Recorremos todos los steps
    for step in steps:
        # En el caso de que se haya pasado el limite hasta el que se había resuelto numericamente las ecuaciones de lotka volterra, actualizamos los datos
        if step > lim_theoretical_step:

            if initial_state == True:
                conejos = conejos[-ventana:]
                lobos = lobos[-ventana:]
                data_loktavolterra(x_init, [steps[0], ventana])
                initial_state = False
            else:
                params = estimate(conejos, lobos)

                # data_loktavolterra(x_init, [lim_theoretical_step,lim_theoretical_step+ventana])
                data_loktavolterra(x_init, [0, ventana])
                lim_theoretical_step += ventana

        if np.max(sol_lv.t) <= ventana:
            step_adaptado = step
            while step_adaptado > ventana:
                step_adaptado -= ventana
            step = step_adaptado
        # Cojemos el indice tal que se aproxime más a nuestro step, ya que en la resolucion se va de 0.0X en 0.0X
        t_idx = np.argmin(np.abs(sol_lv.t - step))

        # Cojemos los valores de 'conejos' y 'lobos' en t=step
        num_conejos = sol_lv.y[0][t_idx]
        num_lobos = sol_lv.y[1][t_idx]

        contadores_teoricos.append((math.ceil(num_lobos), math.ceil(num_conejos)))

    # Devolvemos esos contadores
    return contadores_teoricos

def get_graph_data_dup(datos_nuevos):
    '''
    Funcion que devuelve una lista con elementos de la forma (step, (presa, depredador), (prediccion_presa, prediccion_depredador)) 

    Params:
        -datos_nuevos::list Lista de jsons con los logs del modelo
    '''
    
    datos_validos = []

    step = 0
    cont_lobos = 0
    cont_conejos = 0
    steps = []
    contadores = []

    for i in datos_nuevos:
        step = i["Step"]
        info = i["info"]

        steps.append(step)

        for j in info:
            if "lobo.png" in j.values() and "True" in j.values():
                cont_lobos += 1
            elif "conejo.png" in j.values() and "True" in j.values():
                cont_conejos += 1

        contadores.append((cont_lobos, cont_conejos))
        cont_lobos = 0
        cont_conejos = 0

    # En el caso de que se hayan recogido datos, poner los steps, los contadores actuales y los contadores teoricos
    if len(steps) >= 2:
        # print("len(steps) >= 2")
        theorical_data = get_loktavolterra_data(steps, contadores)
        datos_validos = [steps, contadores, theorical_data]

    datos_validos = [i for i in zip(steps, contadores, theorical_data)]

    return datos_validos


@cross_origin()
@app.route("/paint_data")
def paint_data():
    '''
        Ruta que devuelve los datos necesarios para la representación de la simulación y para la gráfica
        La simulación usa todos los datos/logs del modelo
        La gráfica solo usa el step y, mediante el tratamiento de los datos, contadores de la población teorica y simulada
    '''

    datos_validos = []
    datos_nuevos = []

    if "1" in datosMesa:
        datos_nuevos = datosMesa["1"]
        # Necesitamos como mínimo para poder estimar, 2 datos
        if len(datos_nuevos) < 2:
            return datos_validos
        datosMesa["1"] = []
    else:
        datos_nuevos = []

    if not datos_nuevos:
        return datos_nuevos

    # Recogemos los datos para la grafica
    datos_validos = get_graph_data_dup(datos_nuevos)

    response = make_response(json.dumps([datos_nuevos, datos_validos]))
    
    response.content_type = "application/json"

    return response


if __name__ == "__main__":
    try:
        os.mkdir("users_models")
    except:
        pass
    app.run(debug=True)
