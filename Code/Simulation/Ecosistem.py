import random
import mesa
import Agents
import numpy as np
import random


class Ecosistem(mesa.Model):

    def __init__(self, agent_dict, size, basic_food_info, verbose = False):
        '''
        Clase que modela el ecosistema. Entorno en el que se desarrollan los agentes.

        Params:
            -agent_dict::dict información formateada con los parámetros de cada especie
            -size::int tamaño de la cuadricula
            -basic_food_info::dict información formateada con los parámetros del alimento base
            -verbose::bool habilita opciones de debug
        '''

        self.size = size 
        self.verbose = verbose 
        self.agent_collection = {}
        self.basic_food_info = basic_food_info
        self.grid = mesa.space.MultiGrid(size, size, True)
        self.schedule = mesa.time.RandomActivation(self)
        self.killed = [] # Lista de agentes que morirán en la próxima ronda
        self.mating = [] # Lista de agentes padres reproduciendose
        self.reproduce = [] # Lista de agentes que nacerán en la próxima ronda
        self.next_agent_id = 0 # Contador del id único que necesitan los nuevos agentes
        self.agent_dict=agent_dict 
        self.agentList = [] # Lista completa de agentes 

        for agent in agent_dict:
            self.agent_collection[agent] = []
            for i in range(agent_dict[agent]["amount"]):
                self._copyAgent(agent_dict[agent]["basic_object"])

    def step(self):
        '''
        Ejecuta todas las acciones necesarias para una iteración. Imprime por salida estandar los resultados.
        '''
        print('{"Step": ' + str(self.schedule.steps) + ', "info":[', end="")
        self.schedule.step()
        

        for parent in self.reproduce:
            self._copyAgent(parent, pos = parent.pos)
        self.reproduce = []

        for dead_agent in self.killed:
            try:
                dead_agent.print_log()
                self.agent_collection[dead_agent.specie].remove(dead_agent)
                self.grid.remove_agent(dead_agent)
                self.schedule.remove(dead_agent)
            except:
                pass
        self.killed = []
        for agent in self.agent_dict:
            if len(self.agent_collection[agent])==0:
                for i in range(self.agent_dict[agent]["amount"]):
                    self._copyAgent(self.agent_dict[agent]["basic_object"])

        if not len(self.agent_collection[self.basic_food_info["agent"]])> 7:
            self._create_basic_food()
        print("]}\n")
    
    def _copyAgent(self,agent, pos = None):
        '''
        Crea una copia de un agente basado en un padre existente. Lo añade al scheduler

        Params:
            -agent::Agent Agente padre
            -pos::tuple tupla con la posición del agente en la cuadrícula
        
        Return: Agents.Agent Agente hijo con los parámetros del padre
        '''
        new_agent = Agents.Agent(self.next_agent_id, self, agent.specie, agent.preys, agent.predators,
                                  agent.direction, agent.color, agent.sprite, agent.max_energy, repro_min_energy= agent.repro_min_energy, repro_cost=agent.repro_cost,
                                    move_cost=agent.move_cost, eat_recover=agent.eat_recover, isBasic = agent.isBasic)
        self.agent_collection[agent.specie].append(new_agent)
        self.schedule.add(new_agent)
        if not pos:
            pos = ( self.random.randrange(self.size), self.random.randrange(self.size) )
        self.grid.place_agent(new_agent, pos)
        self.next_agent_id += 1
        return new_agent

                
    def _create_basic_food(self):
        '''
        Genera agentes de comida básica. Los añade a la cuadrícula. La lógica de generación crea 
        clusters de comida básica en la cuadrícula con probabilidad "cluster_prob" hasta un máximo de
        "regen" agentes.
        '''
        for i in range(self.basic_food_info["regen"]):
            agent = random.choice(self.agent_collection[self.basic_food_info["agent"]])
            new_pos = None
            if random.random() < self.basic_food_info["cluster_prob"]:
                try:
                    new_pos = ((agent.pos[0]+random.randint(-1,1))%self.size,(agent.pos[1]+random.randint(-1,1))%self.size)  
                except:
                    pass
            self._copyAgent(agent, new_pos)
    
    def give_reward(self,agent):
        '''
        Función de recompensa del modelo. El modelo otorga la recompensa a los agentes.

        Params:
            -agent::Agents.Agent objeto agente 
        '''
        cellmates=self.grid.get_cell_list_contents([agent.pos])
        num_total_species=0
        for agents in self.agent_collection:
            num_total_species+=(len(self.agent_collection[agents]))
        
        num_near_preys = len([0 for agents in cellmates if agents.specie in agent.preys])
        num_near_predators = len([0 for agents in cellmates if agents.specie in agent.predators])
        num_near_allies=len([0 for agents in cellmates if agents.specie==agent.specie])


        reward=agent.specie.get_reward(num_near_allies,num_near_preys,num_near_predators,num_total_species,agent)
        return reward


    