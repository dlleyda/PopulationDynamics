import mesa
import random
import json
import operator
import numpy as np

RELATIVE_POSITIONS = [(-1, 1), (0, 1), (1, 1), (-1, 0), (0, 0), (1, 0), (-1, -1),
                              (0, -1), (1, -1)]

class Agent(mesa.Agent):
    '''Clase agente genérico'''
    def __init__(self, unique_id, model, specie, preys, predators, direction, color, sprite, energy, repro_min_energy=50, repro_cost=50, move_cost=1, eat_recover=30, isBasic = False):
        super().__init__(unique_id, model)
        self.max_energy = energy # Energía máxima de la que dispone
        self.energy = energy/2 # Energía actual del agente
        self.specie = specie # Objeto de la clase
        self.preys = preys # Lista de objetos de comportamiento (inteligencias) que tienen sus presas
        self.predators = predators # Lista de objetos de comportamiento (inteligencias) que tienen sus depredadores
        self.direction = direction # Tupla, dirección relativa al agente que indica hacia donde mira. Valores posibles: RELATIVE_POSITIONS
        self.color = color # Valor del color necesario para la visualización del objeto en un servidor de mesa
        self.sprite = sprite # Imagen del agente en la visualización de front
        self.repro_min_energy = repro_min_energy # Energía mínima que necesita un agente para reproducirse
        self.repro_cost = repro_cost # Coste de energía asocidado a reproducir al agente
        self.move_cost = move_cost # Coste de energía asociado al movimiento del agente
        self.eat_recover = eat_recover # Cantidad de energía que recupera el agente al comer
        self.isBasic = isBasic # Booleano que determina si es alimento basico o especie inteligente
        self.pos_matriz_pesos = [] # Posiciones de la matriz de pesos
        self.alive = True # Booleano que indica si el agente ha muerto o sigue vivo
    
    def step(self):
        '''
        Ejecuta las acciones de cada agente:
            Los agentes solo pueden ejecutar acciones si les queda energía.
            Cada agente percibe su entorno, se mueve, come, se reproduce y aprende.
        Imprime un log con el estado del agente tras hacer sus acciones.
        '''
        if not self.isBasic:
            if self.energy > 0:
                features = self.perceive() 
                self.move(features)
                self.eat()
                self.reproduce()
                reward = self.model.give_reward(self)
                features = self.perceive() # Necesario para el feedback
                self.specie.feedback(self.pos, features, reward)
            else:
                self.alive = False
                self.model.killed.append(self)

        self.print_log()
    
    def print_log(self):
        '''Imprime la información del estado actual de un agente'''
        log = {"ID": int(self.unique_id),
               "Position": tuple(self.pos),
               "Direction": self.direction,
               "Sprite": self.sprite,
               "Alive": str(self.alive)}
        print(json.dumps(log), end=", ")
    
    def perceive(self):
        '''
        Evalua todas las celdas a su alrededor y le asigna una puntuación de riesgo a cada una.
        Combina las evaluaciones individuales de las celdas adyacentes con la ponderación de la visión.

        Return: lista de riesgos asociados a las 8 celdas adyacentes a una dada (laterales y diagonales)
        '''
        cells_number = 9
        features = []
        
        # posiciones ordenadas de la cuadricula recorridas de manera circular en lugar de lineal
        vision_wheel = [0,1,2,5,8,7,6,3] 
        # pesos para cada posición relativa recorriendo relative_position desde self.direction de manera circular
        vision_wheel_weights = [1,0.5,0.1,-0.5,-1,-0.5,0.1,0.5] 

        #Evaluación preliminar
        for i in range(cells_number):
            pos_to_evaluate = tuple(map(operator.add, self.pos, RELATIVE_POSITIONS[i]))
            pos_to_evaluate = map(lambda x: x % self.model.size, pos_to_evaluate)
            features.append(self.individual_cell_evaluation(*pos_to_evaluate))
        
        #Evitar que no vea nada y capturar el indice de la posición de la dirección
        if self.direction == (0,0):
            direction_index = random.choice(vision_wheel)
            self.direction = RELATIVE_POSITIONS[direction_index]
        else:
            direction_index = RELATIVE_POSITIONS.index(self.direction)
        
        #Evaluación de las celdas en la dirección de la visión
        vision_result = self.__vision_evaluation()
        #Agregar los resultados en orden circular (evitando modificar la casilla (0,0))
        for i in range(len(vision_wheel)):
            features[vision_wheel[(direction_index+i)%len(vision_wheel)]] += vision_result*vision_wheel_weights[i]
            features[vision_wheel[(direction_index+i)%len(vision_wheel)]] /=2

        return features

    def move(self, features):
        '''
        Mueve al agente a una nueva posición. Delega la elección de la celda a la que moverse a su 
        objecto specie.

        Params:
            -features::float[][] matriz de riesgos
        '''
        new_position = self.specie.make_choice(features, self.pos)
        self.direction = (new_position[0]-self.pos[0], new_position[1]-self.pos[1])
        self.energy -= self.move_cost
        self.model.grid.move_agent(self, new_position)

    def eat(self):
        '''
        Si es posible, alimenta al agente con alguna presa que haya en esa misma casilla. Recupera su
        energía en base al parámetro eat_recover
        '''
        cellmates = self.model.grid.get_cell_list_contents([self.pos])
        enemies = [agent for agent in cellmates if agent.specie in self.preys and agent.alive]
        if len(enemies) >= 1:
            other_agent = self.random.choice(enemies)
            self.model.killed.append(other_agent)
            self.energy +=self.eat_recover
            other_agent.alive = False

    def reproduce(self):
        '''
        Si es posible, el agente se reproduce. Informa al ecosistema del naciemiento de un nuevo agente.
        Retira la energía del coste de reproducción agente al padre.
        '''
        cellmates = self.model.grid.get_cell_list_contents([self.pos])
        allies = [agent for agent in cellmates if agent.specie == self.specie]
        if  self.energy > self.repro_min_energy: #and len(allies) > 1:
            other_agent = self.random.choice(allies)
            self.model.mating.append((self, other_agent))
            self.energy -= self.repro_cost
            self.model.reproduce.append(self)

    def individual_cell_evaluation(self, x, y):
        '''
        Devuelve el riesgo plano asociado a una celda individual.

        Params:
            -x::int Coordenada horizontal a evaluar
            -y::int Coordenada vertical a evaluar
        
        Return: float valor del riesgo
        '''
        content = self.model.grid.get_cell_list_contents((x, y))
        try:
            t = len(content)
            p = len([agent for agent in content if type(agent.specie) in self.preys])
            d = len([agent for agent in content if type(agent.specie) in self.predators])

            e = self.energy
            evaluation = (p * (1 - e / 100) ** 2 - d * (e / 100) ** 2) / t

        except ZeroDivisionError as zd:
            evaluation = 0
        
        if(evaluation==0):
            evaluation=np.random.random()*2-1
        return evaluation
    
    def __vision_evaluation(self):
        '''
        Evalúa el conjunto de celdas en el triángulo de visión de un agente.

        Return: float valor agregado de las celdas visibles
        '''
        vision = self.__get_vision(2)
        result = 0
        for i in range(len(vision)):
            pos_to_evaluate = tuple(map(operator.add, self.pos, vision[i][0]))
            pos_to_evaluate = tuple(map(lambda x: x % self.model.size, pos_to_evaluate))
            try:
                result+= self.individual_cell_evaluation(*pos_to_evaluate)/vision[i][1]
            except ZeroDivisionError:
                result+= self.individual_cell_evaluation(*pos_to_evaluate)
        return result*2/len(vision)
    
    def __get_vision(self, dist):
        '''
        Obtiene las celdas en el triángulo de visión de un agente. 
        
        Params:
            -dist::int Distancia de visión del agente en número de casillas
        
        Return: lista de tuplas ((i,j),d) con (i,j) coordenadas cartesianas de
                la celda visible y d la distancia a la celda
        '''
        fov = []
        dif = tuple(map(operator.sub, self.direction, self.pos))
        rev = dif[::-1]
        for i in range(dist):
            pos = tuple(map(operator.add, self.pos, dif))
            fov.append((pos,i))
            if dif[0] == 0 or dif[1] == 0:
                for j in range(1, i + 1):
                    y = tuple([k * j for k in rev])
                    fov.append((tuple(map(operator.sub, pos, y)),i))
                    fov.append((tuple(map(operator.add, pos, y)),i))
            else:
                for j in reversed(range(1, i + 1)):
                    fov.append(((pos[0] - dif[0] * j, pos[1]),i))
                    fov.append(((pos[0], pos[1] - dif[1] * j),i))

        return fov     

class IntelligentBehaviour():
    def __init__(self, type_animal, grid, exploration_rate, discount_factor, 
                 learning_rate,reward_dict):
        '''
        Clase que modela el comportamiento inteligente de una especie mendiante aprendizaje por refuerzo.
        Generalmente existirá una sola clase comportamiento para toda una especie. Es decir, modelan el instinto 
        de dicha especie. Adquirirá el conocimiento colectivo de todos sus individuos y todos estos harán acciones
        en base a esto.

        Params:
            -type_animal::int Atributo temporal por compatibilidad con la version anterior
            -grid::tuple(int,int) Dimensiones del entorno en el que actuan los agentes 
            -exploration_rate::float Probabilidad de elegir una acción aún no explorada. Valores entre [0,1]
            -discount_factor:: float Modifica el valor del algoritmo Q-Learning para hacer estrategias a corto o largo plazo.
            -learning_rate::float Tasa de aprendizaje
        Raises:
            -ValueError: la probabilidad de exploración debe estar contenida en el intervalo [0,1]
        '''
        
        if exploration_rate < 0 or exploration_rate > 1:
            raise ValueError("La probabilidad de exploración debe estar contenida en el intervalo [0,1]")
        self.grid = grid
        self.type_animal = type_animal
        self.epsilon = exploration_rate
        self.weight_matrix = [[0 for i in range(grid[0])] for j in range(grid[1])]  # Posible mejora de arquitectura
        self.discount_factor = discount_factor
        self.learning_rate = learning_rate
        self.relative_positions = {0: (-1, 1), 1: (0, 1), 2: (1, 1), 3: (-1, 0), 4: (0, 0), 5: (1, 0), 6: (-1, -1),
                                   7: (0, -1), 8: (1, -1)}
        
        self.reward_dict=reward_dict

    def __change_position(self, x_position, y_position, perceive_features):
        '''
        Elige la posición del próximo movimiento. Realiza una nueva acción aleatoria con probabilidad
        exploration_rate (self.epsilon). 
        
        Params:
            -x_position::int coordenada horizontal absoluta del agente
            -x_position::int coordenada vertical absoluta del agente
            -perceive_features::float[][] matriz de percepción del entorno
        Return: 
            -tuple(int,int) próximo movimiento
        '''
        r = np.random.rand()

        if r < 1 - self.epsilon:
            list_weights = self.__convert_list_weights((x_position, y_position))

            wanted_scores_array = (np.multiply(np.array(perceive_features), list_weights)).tolist()

            wanted_score = np.max(wanted_scores_array)
            x_move, y_move = self.relative_positions[wanted_scores_array.index(wanted_score)]
            x_move, y_move = x_move + x_position, y_move + y_position
        else:
            x_move = (x_position + np.random.randint(-1, 2))
            y_move = (y_position + np.random.randint(-1, 2))
        new_position = (x_move, y_move)
        return new_position

    def make_choice(self, features, pos):
        '''
        Elige el próximo movimiento. 

        Params:
            -features::float[][] matriz de percepcion
            -pos::tuple(int, int) posición absoluta del agente en el entorno
        Return: 
            -tuple(int,int) próximo movimiento
        '''
        new_position = self.__change_position(*pos, features)
        return new_position
    


    def feedback(self, pos, features, reward):
        '''
        Función de aprendizaje. Actualiza los pesos del modelo en funcion de un estado y su correspondiente recompensa.

        Params:
            -pos::tuple(int, int) posición absoluta del agente en el entorno
            -features::float[][] matriz de riesgos
            -reward::float valor de la recompensa asociada a la ultima acción
        '''
        list_weights = self.__convert_list_weights(pos)
        new_list_weights = self.__update_weight(reward, list_weights, features)

        contador = 0
        for i, j in self.pos_matriz_pesos:
            self.weight_matrix[i][j] = new_list_weights[contador]
            contador += 1

    def __convert_list_weights(self, pos):
        '''
        Obtiene la lista de pesos asociada a una posición
        
        Params:
            -pos::tuple (i,j) coordenadas cartesianas de la posición del agente
        
        Return: list Lista de pesos
        '''
        cells_number = 9
        lista_pos = []
        lista_weights = []
        relative_positions = {0: (-1, 1), 1: (0, 1), 2: (1, 1), 3: (-1, 0), 4: (0, 0), 5: (1, 0), 6: (-1, -1),
                              7: (0, -1), 8: (1, -1)}
        for i in range(cells_number):
            pos_to_evaluate = tuple(map(operator.add, pos, relative_positions[i]))
            pos_to_evaluate = map(lambda x: x % self.grid[0], pos_to_evaluate)
            lista_pos.append(list(pos_to_evaluate))
        self.pos_matriz_pesos = lista_pos

        for i, j in lista_pos:
            lista_weights.append(self.weight_matrix[i][j])

        return lista_weights
    
    def __update_weight(self, reward, list_weights, features):
        '''
        Actualiza la matriz de pesos del agente.

        Params:
            -reward::float recompensa asociada a una acción
            -list_weights::list lista de pesos
            -features::list lista de riesgos de las celdas adyacentes al agente
        '''
        learning_rate = self.learning_rate
        discount_factor = self.discount_factor

        # Compute the Q'-table:
        Q_prime = []
        Q_prime=(self.__get_QFunction(features,list_weights)) 

        # Update the weights:
        Q_prime_max = max(Q_prime)
        for i in range(0, len(list_weights)):
            w = list_weights[i]
            f = features[i]
            list_weights[i] = w + learning_rate * (reward + discount_factor * Q_prime_max - w) 

        return list_weights

    def __get_QFunction(self, features, weights):
        '''
        Computa la QFunction necesaria para el aprendizaje por refuerzo
        
        Params:
            -features::list lista de riesgos de las celdas adyacentes al agente
            -weights::list lista de pesos
        '''
        Q = []
        for i in range(len(weights)):
            Q.append(weights[i] *features[i])

        return Q
    

    def __evaluate_energy_modifier(self,actual_energy,max_energy):
        '''
        Devuelve el coeficiente de recompensa/castigo asociado al nivel de energía

        Params:
            -actual_energy::int energía del agente
            -max_energy::int energía máxima
        '''
        lowest_energy_high_bound=20 
        if(actual_energy < max_energy):
            if(actual_energy < lowest_energy_high_bound):
                coeff_modifier_energy=-self.reward_dict["lowest_energy_modifier"]*actual_energy/max_energy
            else:
                coeff_modifier_energy=-actual_energy/max_energy
        else:
            coeff_modifier_energy=actual_energy/max_energy
        
        return coeff_modifier_energy

    def get_reward(self,num_allies,num_near_preys,num_near_predators,num_total_species,agent):
        '''
        Obtiene la recompensa asociada a una acción según la lógica definida por los parámetros de comportamiento.

        Params:
            -num_allies::int número de agentes de la misma especie que self
            -num_near_preys::int número de presas en las casillas adyacentes
            -num_near_predators::int número de depredadores en las casillas adyacentes
            -num_total_species::int número total de agentes en las casillas adyacentes
            -agent::agente que recibe la recompensa 

        '''
        coefficient_normalization_value=4

        if(num_near_predators>0):
            coeff_modifier_near_predator=(-num_near_predators/num_total_species)*self.reward_dict["near_predator_positive_modifier"]
        else:
            coeff_modifier_near_predator=self.reward_dict["near_predator_negative"]

        if(num_near_preys>0):
            coef_modifier_near_prey=(num_near_preys/num_total_species)*self.reward_dict["near_prey_positive_modifier"]
        else:
            coef_modifier_near_prey=self.reward_dict["near_prey_negative"]
        
        if(num_allies>0):
            coeff_modifier_near_ally=num_allies/num_total_species * self.reward_dict["near_allies_positive_modifier"]
        else:
            coeff_modifier_near_ally=self.reward_dict["near_allies_negative"]
        

        coeff_modifier_energy=self.__evaluate_energy_modifier(agent.energy,agent.max_energy)
        

        reward = (coeff_modifier_near_ally+coeff_modifier_near_predator+coef_modifier_near_prey+coeff_modifier_energy)/coefficient_normalization_value

        return reward

class DumbBehaviour():
    def __init__(self):
        '''
        Clase que modela el comportamiento inerte de especies como el alimento base
        '''
        pass

    def make_choice(self, features, pos):
        '''
        Decide no hacer acción, ignora la información del ecosistema
        '''
        return pos

    def get_reward(num_allies,num_near_preys,num_near_predators,total_species,energy,max_energy):
        """
        No utiliza las recompensas
        """
        return 0

    def feedback(self, pos, features, reward):
        '''
        No aprende
        '''
        return None
