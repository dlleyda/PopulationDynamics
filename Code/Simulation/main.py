import mesa
from Ecosistem import Ecosistem
import Agents

def agent_portrayal(agent):
    portrayal = {
        "Shape": "circle",
        "Filled": "true",
        "Layer":0,
        "text":", ener:" +str(agent.energy),
        "Color": agent.color,
        "r": 1,
    }
    return portrayal

SIZE = 10
LEARNING_RATE = 0.1
DISCOUNT_FACTOR=0.9
NUMBER_OF_PREYS = 5
NUMBER_OF_PREDATORS = 4
NUMBER_OF_GRASS = 15

BASIC_FOOD_REGEN = 1
BASIC_FOOD_CLUSTER_PROB = 0.85

# PREDATORS BEHAVIOURS MODIFIER FOR REWARD FUNCTION
PRED_NEAR_PREDATOR_NEGATIVE_REWARD=-1
PRED_NEAR_PREY_NEGATIVE_REWARD=-1
PRED_NEAR_ALLIES_NEGATIVE_REWARD=-0.3
PRED_NEAR_PREDATOR_POSITIVE_MODIFIER=1
PRED_NEAR_PREY_POSITIVE_MODIFIER=0.5
PRED_NEAR_ALLIES_POSITIVE_MODIFIER=0.3
PRED_LOWEST_ENERGY_MODIFIER=2

# PREYS BEHAVIOURS MODIFIER FOR REWARD FUNCTION
PREY_NEAR_PREDATOR_NEGATIVE_REWARD=-1
PREY_NEAR_PREY_NEGATIVE_REWARD=-1
PREY_NEAR_ALLIES_NEGATIVE_REWARD=-0.2
PREY_NEAR_PREDATOR_POSITIVE_MODIFIER=1
PREY_NEAR_PREY_POSITIVE_MODIFIER=0.1
PREY_NEAR_ALLIES_POSITIVE_MODIFIER=0.3
PREY_LOWEST_ENERGY_MODIFIER=3


prey_reward_dict = {"near_predator_negative":PREY_NEAR_PREDATOR_NEGATIVE_REWARD,"near_prey_negative":PREY_NEAR_PREY_NEGATIVE_REWARD,
                    "near_allies_negative":PREY_NEAR_ALLIES_NEGATIVE_REWARD,"near_predator_positive_modifier":PREY_NEAR_PREDATOR_POSITIVE_MODIFIER,
                    "near_prey_positive_modifier":PREY_NEAR_PREY_POSITIVE_MODIFIER,"near_allies_positive_modifier":PREY_NEAR_ALLIES_POSITIVE_MODIFIER,
                    "lowest_energy_modifier":PREY_LOWEST_ENERGY_MODIFIER}

predator_reward_dict = {"near_predator_negative":PRED_NEAR_PREDATOR_NEGATIVE_REWARD,"near_prey_negative":PRED_NEAR_PREY_NEGATIVE_REWARD,
                    "near_allies_negative":PRED_NEAR_ALLIES_NEGATIVE_REWARD,"near_predator_positive_modifier":PRED_NEAR_PREDATOR_POSITIVE_MODIFIER,
                    "near_prey_positive_modifier":PRED_NEAR_PREY_POSITIVE_MODIFIER,"near_allies_positive_modifier":PRED_NEAR_ALLIES_POSITIVE_MODIFIER,
                    "lowest_energy_modifier":PRED_LOWEST_ENERGY_MODIFIER}


prey_behaviour = Agents.IntelligentBehaviour(1, (SIZE, SIZE), 0.08, DISCOUNT_FACTOR, LEARNING_RATE,prey_reward_dict)
predator_behaviour = Agents.IntelligentBehaviour(0, (SIZE, SIZE), 0.08, DISCOUNT_FACTOR, LEARNING_RATE,predator_reward_dict)
grass_behaviour = Agents.DumbBehaviour()

basic_predator_agent = Agents.Agent(None, None, predator_behaviour, [prey_behaviour], [], (1,0), "red","lobo.png", 100, repro_min_energy= 70, repro_cost=50,
                                    move_cost=2, eat_recover=40)
basic_prey_agent = Agents.Agent(None, None, prey_behaviour, [grass_behaviour], [predator_behaviour], (1,0), "green", "conejo.png", 100)
basic_grass_agent =  Agents.Agent(None, None, grass_behaviour, [], [prey_behaviour], [], "grey","cesped.png", 200, isBasic=True)

agent_dict = {
    prey_behaviour:{"amount":NUMBER_OF_PREYS, "basic_object":basic_prey_agent},
    predator_behaviour:{"amount":NUMBER_OF_PREDATORS, "basic_object":basic_predator_agent},
    grass_behaviour:{"amount":NUMBER_OF_GRASS, "basic_object":basic_grass_agent}
}

basic_food_info = {
    "agent":grass_behaviour,
    "regen":BASIC_FOOD_REGEN,
    "cluster_prob":BASIC_FOOD_CLUSTER_PROB
}


############################# VISUALIZACIÓN CON EL SERVIDOR DE MESA#############################
grid = mesa.visualization.CanvasGrid(agent_portrayal, SIZE, SIZE, 500, 500)
server = mesa.visualization.ModularServer(
    Ecosistem, [grid], "Ecosistem", {"agent_dict":agent_dict, "size": SIZE,"basic_food_info":basic_food_info}
)
server.port = 8526  # The default
server.verbose = False
server.launch()


############################ SERVIDOR PROPIO #########################
# model = Ecosistem(agent_dict, SIZE, basic_food_info, verbose=True)
# for i in range(70):
#     model.step()
