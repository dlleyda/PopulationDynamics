''''
Interfaz de comunicación entre el servidor y la simulación. 

RECIBE POR PARÁMETROS LA RUTA AL ARCHIVO DE CONFIGURACIÓN

Recupera la instancia serializada de un Ecosistema. 

Ejecuta la simulación un número determinado de steps. Presente en config.json

Guarda el estado del modelo en la misma ruta que estuviera su archivo de configuración
'''

import mesa
import sys
import json
from Ecosistem import Ecosistem
import Agents
import pickle

JSON_NAME_CONFIG="config.json"
if len(sys.argv) > 1:
    with open(sys.argv[1]+JSON_NAME_CONFIG) as f:
        data = json.load(f)
    
PICKLE_FILENAME="model.pickle"

def cargar_modelo(ruta):
    file=open(ruta+PICKLE_FILENAME,"rb")
    loaded_model=pickle.load(file)
    file.close()
    return loaded_model


def guardar_modelo(modelo,ruta):
    file = open(ruta+PICKLE_FILENAME, 'wb')
    pickle.dump(modelo,file)
    file.close()


model=cargar_modelo(sys.argv[1])
for i in range(data["ecosistem"]["iters"]):
    model.step()
guardar_modelo(model,sys.argv[1])

