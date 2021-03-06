from mesa import Model, Agent
from mesa.time import RandomActivation
from mesa.space import SingleGrid
from mesa.datacollection import DataCollector

import random

'''
Optional for coupling of the Schelling model
- Migration
    - The net amount of agent change per step needs to be zero.
    - Random agents are removed? Or unhappy agents? It should be unhappy ones - that makes more sense at least.
    - Type 0 agents leaving must be replaced by type 1 agents.
    - Type 1 agents leaving must be replaced by type 0 agents.
    - Where are new agents incoming placed onto the map? Random locations
    - Is there a constant turnover? Or is it a one time thing? Dor policy instruments, it makes more sense to have a continuous turnover of a certain percentage

Things that are needed:
- The belief tree has been changed - there is a need for the calculation of new KPIs that will fit within the issue tree

Things that might be needed:
- Move the happiness KPI calculation to after the step function. Right now, the calculation is slightly inaccurate as it is done throughout the simulation itself and not at its end.
- Add a radius to moving the agents

KPIs:
What needs to be recorded (KPIs):
Empty cells -- Implemented
Type 0 -- Implemented
Type 1 -- Implemented
Vision - Global - Implemented
Movement - Global - Implemented
Last movement (agent individual) - Implemented
Type 0 homophily - Implemented
Type 1 homophily - Implemented
Evenness - Implemented
Policy core 1 KPI (movement) - Implemented
Policy core 2 KPI (happiness) - Implemented
Happiness of type 0 agents - Implemented
Happiness of type 1 agents - Implemented
Movement of type 0 agents - Implemented
Movement of type 1 agents - Implemented

'''

class SchellingAgent(Agent):
    '''
    Schelling segregation agent
    '''
    def __init__(self, pos, model, agent_type, last_move):
        '''
         Create a new Schelling agent.
         Args:
            unique_id: Unique identifier for the agent.
            x, y: Agent initial location.
            agent_type: Indicator for the agent's type (minority=1, majority=0)
        '''
        super().__init__(pos, model)
        self.pos = pos
        self.type = agent_type
        self.last_move = last_move

    def step(self):

        # Checking if the agent is happy
        happyBool = self.happy_check()            

        # Increment last move parameter
        self.last_move += 1

        # If unhappy, move - considering the movement quota and whether the agent is type0 or type1:
        movementQuotaCheck = self.model.movementQuota*self.model.schedule.get_agent_count()
        if happyBool == False:
            if self.model.movementQuotaCount <= movementQuotaCheck:
                # check if the agent has not moved within the last X rounds
                if self.last_move > self.model.last_move_quota: 
                    self.model.grid.move_to_empty(self)
                    self.model.movementQuotaCount += 1
                    self.model.movement += 1
                    if self.type == 0:
                        self.model.movementtype0 += 1
                    if self.type == 1:
                        self.model.movementtype1 += 1
                    # Update happiness status after move
                    self.happy_check()

                    # reset the movement parameter for the agent
                    self.last_move = 0


    def happy_check(self):

        '''
        Function used to check if the agent is happy in its current position. Use for checking if there is a need to move and to check if the location it is moving to is appropriate.
        '''
        # Initialisation of patameters
        similar = 0
        happyBool = bool()

        # Finding the neighbors
        neighborList = self.model.grid.get_neighbors(self.pos, True, False, self.model.happyCheckRadius)

        # Iterating through the neighbors to find whether they are similar:
        for neighbor in neighborList:
            if neighbor.type == self.type:
                similar += 1

        # Converting similarity value into a percentage
        if len(neighborList) != 0:
            similar = similar/len(neighborList)
        else:
            similar = 0

        if (self.type == 0 and similar > self.model.homophilyType0) or (self.type == 1 and similar > self.model.homophilyType1):
            happyBool = True
            self.model.happy += 1
            if self.type == 0:
                self.model.happytype0 += 1
            if self.type == 1:
                self.model.happytype1 += 1

        return happyBool


class Schelling(Model):
    '''
    Model class for the SM coupled to the Schelling segregation model.
    This class has been modified from the original mesa Schelling model.
    '''

    def __init__(self, height=20, width=20, density=0.8, minority_pc=0.2, homophilyType0=0.5, homophilyType1=0.5, movementQuota=0.30, happyCheckRadius=5, moveCheckRadius=10, last_move_quota=5):
        '''
        '''

        self.height = height
        self.width = width
        self.density = density
        self.minority_pc = minority_pc
        self.homophilyType0 = homophilyType0
        self.homophilyType1 = homophilyType1
        self.movementQuota = movementQuota
        self.happyCheckRadius = happyCheckRadius
        self.moveCheckRadius = moveCheckRadius
        self.last_move_quota = last_move_quota

        self.schedule = RandomActivation(self)
        self.grid = SingleGrid(height, width, torus=True)

        self.happy = 0
        self.happytype0 = 0
        self.happytype1 = 0
        self.stepCount = 0
        self.evenness = 0
        self.empty = 0
        self.type0agents = 0
        self.type1agents = 0
        self.movement = 0
        self.movementtype0 = 0
        self.movementtype1 = 0
        self.movementQuotaCount = 0
        self.numberOfAgents = 0
        self.datacollector = DataCollector(
            # Model-level count of happy agents
            {"step": "stepCount", "happy": "happy", "happytype0": "happytype0", "happytype1": "happytype1", "movement": "movement", "movementtype0": "movementtype0", "movementtype1": "movementtype1","evenness": "evenness", "numberOfAgents": "numberOfAgents", "homophilyType0": "homophilyType0", "homophilyType1": "homophilyType1", "movementQuota": "movementQuota", "happyCheckRadius": "happyCheckRadius", "last_move_quota": "last_move_quota"},
            # For testing purposes, agent's individual x and y
            {"x": lambda a: a.pos[0], "y": lambda a: a.pos[1], "Agent type": lambda a:a.type})

        # , "z": lambda a:a.type

        # Set up agents
        # We use a grid iterator that returns
        # the coordinates of a cell as well as
        # its contents. (coord_iter)
        for cell in self.grid.coord_iter():
            x = cell[1]
            y = cell[2]
            if self.random.random() < self.density:
                if self.random.random() < self.minority_pc:
                    agent_type = 1
                else:
                    agent_type = 0

                last_move = round(random.random()*10)  # randomly assign a value from 0 to 10
                agent = SchellingAgent((x, y), self, agent_type, last_move)
                self.grid.position_agent(agent, (x, y))
                self.schedule.add(agent)
        # print("Schedule: ", len(self.schedule.agents))

        self.running = True
        self.numberOfAgents = self.schedule.get_agent_count()
        self.datacollector.collect(self)


    def step(self, policy, scenario_input):
        '''
        Run one step of the model. If All agents are happy, halt the model.
        Note on the eveness paramater calculation:
            It cannot be performed in the step function of the agents as then it would not take consider periods of time during which the agents are still moving, making the parameter calculation inaccurate. 
        '''
        self.happy = 0  # Reset counter of happy agents
        self.happytype0 = 0  # Reset counter of happy type 0 agents
        self.happytype1 = 0  # Reset counter of happy type 1 agents
        self.empty = 0  # Reset counter of empty cells
        self.type0agents = 0  # Reset count of type 0 agents
        self.type1agents = 0  # Reset count of type 1 agents
        self.movementQuotaCount = 0  # Reset count of the movement quota
        self.movement = 0  # Reset counter of movement of agents
        self.movementtype0 = 0  # Reset counter of movement of type 0 agents
        self.movementtype1 = 0  # Reset counter of movement of type 1 agents



        # introduction of the selected policy in the Schelling model
        # happy check vision changes
        if policy[0] != None and self.happyCheckRadius<15 and self.happyCheckRadius>1:
            self.happyCheckRadius += policy[0]
        # movement quota changes
        if policy[1] != None and self.movementQuota<1 and self.movementQuota>0.05:
            self.movementQuota += policy[1]
        # last movement threshold
        if policy[2] != None and self.last_move_quota<50 and self.last_move_quota>0:
            self.last_move_quota += policy[2]
        # type 0 preference
        if policy[3] != None and self.homophilyType0<1 and self.homophilyType0>0:
            self.homophilyType0 += policy[3]
        # type 1 preference
        if policy[4] != None and self.homophilyType1<1 and self.homophilyType1>0:
            self.homophilyType1 += policy[4]

        # introduction of changes based on scenarios
        if scenario_input == None:  # check
            scenario_input = [None, None, None, None, None]
        # scenario_input = [happyCheckRadius, movementQuota, last_move_quota, homophilyType0, homophilyType1]
        if scenario_input[0] != None: # happyCheckRadius
            self.happyCheckRadius = scenario_input[0]
        if scenario_input[1] != None: # movementQuota
            self.movementQuota = scenario_input[1]
        if scenario_input[2] != None: # last_move_quota
            self.last_move_quota = scenario_input[2]
        if scenario_input[3] != None: # homophilyType0
            self.homophilyType0 = scenario_input[3]
        if scenario_input[4] != None: # homophilyType1
            self.homophilyType1 = scenario_input[4]

        # run the step for the agents
        self.schedule.step()
        # print(self.movementQuotaCount, " agents moved.")
        # print(round(self.happy/self.schedule.get_agent_count() * 100,2), "percent are happy agents.")

        # calculating empty counter
        self.empty = (self.height*self.width) - self.schedule.get_agent_count()
        # calculating type 0 and type 1 agent numbers
        for agent in self.schedule.agent_buffer(shuffled=True):
            # print(agent.type)
            if agent.type == 0:
                self.type0agents += 1
            if agent.type == 1:
                self.type1agents += 1

        # calculation of evenness (segregation parameter) using Haw (2015).
        self.evenness_calculation()

        # iterate the steps counter
        self.stepCount += 1

        # collect data
        self.datacollector.collect(self)
        

        # checking the datacollector
        # if self.stepCount % 2 == 0:
        #     print(self.datacollector.get_model_vars_dataframe())
        #     print(self.datacollector.get_agent_vars_dataframe())

        if self.happy == self.schedule.get_agent_count():
            self.running = False
            print("All agents are happy, the simulation ends!")

        output_KPIs = [self.evenness, self.movement, self.happy, self.movementtype0, self.movementtype1, self.happytype0, self.happytype1]
        return output_KPIs, self.type0agents, self.type1agents

    def evenness_calculation(self):

        '''
        To calculate the evenness parameter, one needs to first subdivide the grid into areas of more than one square each. The evenness will be then calculated based on the distribution of type 0 and type 1 agents in each of these areas.
        The division into area needs to be done carefully as it depends on the inputs within the model (width and height of the grid).
        '''

        # check for a square grid
        if self.height != self.width:
            self.running = False
            print("WARNING - The grid is not a square, please insert the same width and height")

        # reset the evenness parameter
        self.evenness = 0

        # algorithm to calculate evenness
        n = 4  # number of big areas considered in width and height
        if self.height % n == 0:
            # consider all big areas
            for big_dy in range(n):
                for big_dx in range(n):
                    # looking within one big areas, going through all cells
                    listAgents = []
                    for small_dy in range(int(self.height/n)):
                        for small_dx in range(int(self.height/n)):
                            for agents in self.schedule.agent_buffer(shuffled=True):
                                if agents.pos == (self.height/n * big_dx + small_dx, self.height/n * big_dy + small_dy):
                                    listAgents.append(agents)
                    # calculating evenness for each big area
                    countType0agents = 0  # Reset of the type counter for type 0 agents
                    countType1agents = 0  # Reset of the type counter for type 1 agents
                    # checking the type of agents in the big area
                    for agents in listAgents:
                        if agents.type == 0:
                            countType0agents += 1
                        if agents.type == 1:
                            countType1agents += 1
                    self.evenness += 0.5 * abs((countType0agents/self.type0agents) - (countType1agents/self.type1agents))
        # print("evenness :", round(self.evenness,2))