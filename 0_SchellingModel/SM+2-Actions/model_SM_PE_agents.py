from mesa import Model, Agent
from mesa.time import RandomActivation
from mesa.space import SingleGrid
from mesa.datacollection import DataCollector
import copy
import random

class ActiveAgent(Agent):
    '''
    Active agents, including policy makers, policy entrepreneurs and external parties.
    '''
    def __init__(self, pos, unique_id, model, agent_type, resources, affiliation, issuetree, policytree, conflictLevelIssue, conflictLevelPolicy):
        
        '''
        Args:
            unique_id: Unique identifier for the agent.
            x, y: Agent initial location.
            agent_type: Indicator for the agent's type (minority=1, majority=0)
        '''
        super().__init__(unique_id, model)
        self.pos = pos  # defines the position of the agent on the grid
        self.unique_id = unique_id  # unique_id of the agent used for algorithmic reasons
        self.agent_type = agent_type  # defines the type of agents from policymaker, policyentrepreneur and externalparty
        self.resources = resources  # resources used for agents to perform actions
        self.affiliation = affiliation  # political affiliation affecting agent interactions
        self.issuetree = issuetree  # issue tree of the agent (including partial issue of other agents)
        self.policytree = policytree
        self.conflictLevelIssue = conflictLevelIssue
        self.conflictLevelPolicy = conflictLevelPolicy

        # selected issues and policies
        self.selected_PC = None
        self.selected_PF = None
        self.selected_S = None
        self.selected_PI = None
        self.focus_AS = None
        self.focus_PF = None

    def preference_update(self, agent, who):

        self.model.preference_update_DC(agent, who)

        self.model.preference_update_PC(agent, who)

        self.model.preference_update_S(agent, who)

        self.model.preference_update_PF(agent, who)

    def conflictLevel_update(self, agent, who):

        self.model.conflictLevel_update_issue(agent, who)

        self.model.conflictLevel_update_policy_PF(agent, who)

        self.model.conflictLevel_update_policy_PI(agent, who)

    def selection_focus_AS(self):

        '''
        The agenda setting focus selection function
        ===========================

        This function is used to select which focus the agent will have: issue or policy.

        Note: For the policy families, the preferences have to be first reversed as the best preferences for the policy family is the minimum preference. They can then be compared to the preferences of the policy core issues.

        Note2: Actually, there would be no need to invert it as we don't care about the best PF but just whether we have a PF or a PC as the focus. So it has been commented
        '''

        len_PC = self.model.len_PC
        len_PF = self.model.len_PC

        PCF_pref_list = []
        for i in range(len_PC):
            PCF_pref_list.append(self.issuetree[self.unique_id][self.model.len_DC + i][2])
        for i in range(len_PF):
            PCF_pref_list.append(self.policytree[self.unique_id][0][i][len_PF])

        focus_index = PCF_pref_list.index(max(PCF_pref_list))

        if focus_index < len_PC:
            self.focus_AS = 'i'
        else:
            self.focus_AS = 'p'

        # ''' for the policy core issues'''
        # len_PC = self.model.len_PC
        # # compiling all the preferences
        # PC_pref_list = []
        # for i in range(len_PC):
        #     PC_pref_list.append([self.issuetree[self.unique_id][self.model.len_DC + i][2], self.model.len_DC + i])

        # ''' for the policy families '''
        # len_PF = self.model.len_PC

        # # selection of the preferred policy family
        # # compiling and reversing all the PF preferences
        # PF_pref_list = []
        # for i in range(len_PF):
        #     PF_pref_list.append([self.policytree[self.unique_id][0][i][len_PF], i])

        # def getKey(item):
        #     return item[0]
        # # sorting the list for reversal
        # PF_pref_list = sorted(PF_pref_list, key=getKey)

        # PF_pref_list_RA = []
        # for item in PF_pref_list[::-1]:
        #     PF_pref_list_RA.append(copy.deepcopy(item))

        # for i in range(len(PF_pref_list_RA)):
        #     PF_pref_list_RA[i][1] = copy.deepcopy(PF_pref_list[i][1])

        # ''' focus selection '''
        # PCF_pref_list = []
        # for i in PC_pref_list:
        #     PCF_pref_list.append(i)
        # for i in PF_pref_list_RA:
        #     PCF_pref_list.append(i)

        # focus_index = PCF_pref_list.index(max(PCF_pref_list))

        # if focus_index < len_PC:
        #     self.focus = 'i'
        # else:
        #     self.focus = 'p'

    def selection_focus_PF(self):

        '''
        The policy formulation focus selection function
        ===========================

        This function is used to select which focus the agent will have: issue or policy.

        Note: If there are a lot of policy instruments, the agents will always select a secondary issue as the focus as the preference is more diluted between the policies leading to an almost always preference for the issues.

        '''

        len_DC = self.model.len_DC
        len_PC = self.model.len_PC
        len_S = self.model.len_S

        # considering only issues related to the issue on the agenda
        S_pref_list_indices = []
        for i in range(len_S):
            if self.issuetree[self.unique_id][len_DC+len_PC+len_S+len_DC*len_PC+self.model.agenda_PC*len_S+i][0] !=0:
                S_pref_list_indices.append(i)

        # selecting the policy instrument from the policy family on the agenda
        PFIns_indices = self.model.PF_indices[self.model.agenda_PF]

        # assembling the total list with secondary issues and policy instruments
        SPIns_pref_list = []
        for i in range(len(S_pref_list_indices)):
            SPIns_pref_list.append(self.issuetree[self.unique_id][len_DC+len_PC+S_pref_list_indices[i]][2])
        for i in range(len(PFIns_indices)):
            SPIns_pref_list.append(self.policytree[self.unique_id][1][PFIns_indices[i]][len_S])

        focus_index = SPIns_pref_list.index(max(SPIns_pref_list))

        if focus_index < len(S_pref_list_indices):
            self.focus_PF = 'i'
        else:
            self.focus_PF = 'p'

    def selection_PC(self):

        '''
        This function is used to select the preferred policy core issue for the active agents based on all their preferences for the policy core issues.
        '''

        # compiling all the preferences
        PC_pref_list = [None for k in range(self.model.len_PC)]
        for i in range(self.model.len_PC):
            PC_pref_list[i] = self.issuetree[self.unique_id][self.model.len_DC + i][2]

        # assigning the highest preference as the selected policy core issue
        self.selected_PC = PC_pref_list.index(max(PC_pref_list))

    def selection_PF(self):
        
        '''
        This function is used to select the preferred policy family. First the preferences are calculated. Then the policy family preferred is selected as the policy family with the lowest preference (this means the smallest gap after the introduction of the policy family likelihood).
        '''

        len_PC = self.model.len_PC

        # selection of the preferred policy family
        # compiling all the preferences
        PF_pref_list = [None for k in range(len_PC)]
        for i in range(len_PC):
            PF_pref_list[i] = self.policytree[self.unique_id][0][i][len_PC]

        # assigning the lowest preference as the selected policy family by the agent
        self.selected_PF = PF_pref_list.index(min(PF_pref_list))

    def selection_S(self):

        '''
        This function is used to select the preferred secondary issue. First, only the secondary issues that are related, through a causal relation, to the policy core issue on the agenda are placed into an array. Then, the one with the highest preference is selected. It is then used as the issue that the agent will advocate for later on.

        NOTE: The output (self.selected_S) is provided as a index starting from 0. It is not counted like the secondary issues from 1!
        '''

        len_DC = self.model.len_DC
        len_PC = self.model.len_PC
        len_S = self.model.len_S

        # considering only issues related to the issue on the agenda
        S_pref_list_indices = []
        for i in range(len_S):
            if self.issuetree[self.unique_id][len_DC+len_PC+len_S+len_DC*len_PC+self.model.agenda_PC*len_S+i][0] != 0:
                S_pref_list_indices.append(i)

        S_pref_list = [None for i in range(len(S_pref_list_indices))]
        for i in range(len(S_pref_list)):
            S_pref_list[i] = self.issuetree[self.unique_id][len_DC+len_PC+S_pref_list_indices[i]][2]

        # assigning the highest preference as the selected policy core issue
        self.selected_S = S_pref_list.index(max(S_pref_list))
        # make sure to select the right value in the list of indices (and not based on the index in the list of preferences)
        self.selected_S = S_pref_list_indices[self.selected_S]

    def selection_PI(self):
        
        '''
        This function is used to select the preferred policy instrument from the policy family on the agenda. First the preferences are calculated. Then the policy family preferred is selected as the policy family with the lowest preference (this means the smallest gap after the introduction of the policy family likelihood).
        '''

        len_S = self.model.len_S

        # selecting the policy instrument from the policy family on the agenda
        PFIns_indices = self.model.PF_indices[self.model.agenda_PF]

        # selection of the preferred policy instrument
        # compiling all the preferences
        PI_pref_list = [None for k in range(len(PFIns_indices))]
        for i in range(len(PFIns_indices)):
            PI_pref_list[i] = self.policytree[self.unique_id][1][PFIns_indices[i]][len_S]

        # assigning the lowest preference as the selected policy instrument by the agent
        self.selected_PI = PI_pref_list.index(min(PI_pref_list))
        # print("Index chosen from PFX: ", self.selected_PI)
        # print("self.model.PF_indices", self.model.PF_indices[self.model.agenda_PF])
        self.selected_PI = self.model.PF_indices[self.model.agenda_PF][self.selected_PI]
        # print("Policy instrument selected: ",self.selected_PI)

    def action_AS_issue(self, action_param):

        '''
        The action function for issue focused agents in the agenda setting
        ===========================

        This function is used to calculate the likelihood of an agent performing an action and apply the selected action. This is for the issue focused agents in the agenda setting. The actions allowed are:
        - (Framing 'fra') - Influence on the causal relations above the selected policy core issue
        - (Direct goal influence 'dgoa') - Influence on the goals of the selected policy core issue
        - (Direct belief influence 'dbel') - Influence on the beliefs of the selected policy core issue

        The action with the highest likelihood is selected.

        Note: Full knolwedge is used in this function

        '''

        len_DC = self.model.len_DC
        len_PC = self.model.len_PC
        len_S = self.model.len_S
        issue_number = len_DC + len_PC + len_S


        weightAction = action_param [0]
        weightResources = action_param[1]  # defines how many of the resources are spent per action
        resources_action = self.resources

        # selection of the causal relation of interest
        cr_selec = []
        # only consider the causal relations related to the issue selected by the agent
        for cr_choice in range(len_DC):
            cr_selec.append(len_DC + len_PC + len_S + self.selected_PC + cr_choice*len_DC)

        _iter = 0
        while resources_action > 0.001:

            ''' Calculation of the likelihood '''
            grade_list = []
            grade_list_agents = []
            for agent in self.model.schedule.agent_buffer(shuffled=True):
                if isinstance(agent, ActiveAgent) and agent != self:

                    _unique_id = agent.unique_id
                    grade_list_agents.append(agent)
                            
                    # grading all framing likelihood actions:
                    for cr in cr_selec:
                        cr_grade = self.conflictLevelIssue[_unique_id][cr][0]
                        grade_list.append(round(cr_grade,4)) 

                    # grading belief likelihood change
                    belief_grade = self.conflictLevelIssue[_unique_id][len_DC+self.selected_PC][0]
                    grade_list.append(round(belief_grade,4))

                    # grading aim likelihood change
                    goal_grade = self.conflictLevelIssue[_unique_id][len_DC+self.selected_PC][1]
                    grade_list.append(round(goal_grade,4))

            ''' Selection of the best action '''
            # Check if several actions have the same grade
            max_best_action = max(grade_list)
            count = 0
            count_max_list = []
            for item in grade_list:
                if item == max_best_action:
                    count_max_list.append(count)  # storing the indexes of the grades
                count += 1

            if len(count_max_list) > 1: # if there are several grades at the max level, then choose randomly
                best_action_index = random.choice(count_max_list)
            else:  # if not, the best grade is the maximum
                best_action_index = grade_list.index(max(grade_list))

            # calculating the best action - 0,len(cr_selec) is cr, len(cr_selec)+1 is belief, len(cr_selec)+2 is goal
            best_action = best_action_index - (len(cr_selec) + 2) * int(best_action_index/(len(cr_selec) + 2))

            ''' Implementation of the best action '''
            
            for agent in self.model.schedule.agent_buffer(shuffled=True):
                # make sure to select the right agent onto which the actions is performed
                if isinstance(agent, ActiveAgent) and agent == grade_list_agents[int(best_action_index/(len(cr_selec) + 2))]:

                    _unique_id = agent.unique_id

                    # framing influence action
                    if best_action < len(cr_selec):
                        cr_act = cr_selec[best_action]  # defining the causal relation
                        agent.issuetree[_unique_id][cr_act][0] += (self.issuetree[self.unique_id][cr_act][0] - agent.issuetree[_unique_id][cr_act][0])  * self.resources * weightResources * weightAction
                        agent.issuetree[_unique_id][cr_act][0] = round(agent.issuetree[_unique_id][cr_act][0], 4)

                    # belief influence action
                    if best_action == len(cr_selec):
                        agent.issuetree[_unique_id][len_DC+self.selected_PC][0] += (self.issuetree[self.unique_id][len_DC+self.selected_PC][0] - agent.issuetree[_unique_id][len_DC+self.selected_PC][0])  * self.resources * weightResources * weightAction
                        agent.issuetree[_unique_id][len_DC+self.selected_PC][0] = round(agent.issuetree[_unique_id][len_DC+self.selected_PC][0], 4)

                    # goal influence action
                    if best_action == len(cr_selec) + 1:
                        agent.issuetree[_unique_id][len_DC+self.selected_PC][1] += (self.issuetree[self.unique_id][len_DC+self.selected_PC][1] - agent.issuetree[_unique_id][len_DC+self.selected_PC][1])  * self.resources * weightResources * weightAction
                        agent.issuetree[_unique_id][len_DC+self.selected_PC][1] = round(agent.issuetree[_unique_id][len_DC+self.selected_PC][1], 4)

                    # updating the conflict level after each action
                    self.model.conflictLevel_update_issue(self, agent)
            
            _iter += 1
            resources_action -= self.resources * weightResources

    def action_AS_policy(self, action_param):

        '''
        The action function for policy focused agents in the agenda setting
        ===========================

        This function is used to calculate the likelihood of an agent performing an action and apply the selected action. This is for the policy focused agents in the agenda setting. The actions allowed are:
        - (Likelihood influence 'lik') - Influence on the perceived likelihoods of the policy families
        - (Goal influence 'goa') - Influence on the goals of the associated policy core issues
        - (Belief influence 'bel') - Influence on the beliefs of the associated policy core issues

        The action with the highest likelihood is selected.

        Note: Full knolwedge is used in this function

        '''

        len_PF = self.model.len_PC
        len_DC = self.model.len_DC
        len_PC = self.model.len_PC
        len_S = self.model.len_S
        issue_number = len_DC + len_PC + len_S

        weightAction = action_param [0]
        weightResources = action_param[1]  # defines how many of the resources are spent per action
        resources_action = self.resources

        _iter = 0
        while resources_action > 0.001:

            ''' Calculation of the likelihood '''
            grade_list = []
            grade_list_agents = []
            for agent in self.model.schedule.agent_buffer(shuffled=True):
                if isinstance(agent, ActiveAgent) and agent != self:

                    _unique_id = agent.unique_id
                    grade_list_agents.append(agent)
                            
                    # grading all framing likelihood actions:
                    for lik in range(len_PC):
                        lik_grade = self.conflictLevelPolicy[_unique_id][0][self.selected_PF][lik]
                        grade_list.append(round(lik_grade,4)) 

                    # grading belief likelihood change
                    for belief in range(len_PC):
                        belief_grade = self.conflictLevelIssue[_unique_id][len_DC+belief][0]
                        grade_list.append(round(belief_grade,4))

                    # grading aim likelihood change
                    for goal in range(len_PC):
                        goal_grade = self.conflictLevelIssue[_unique_id][len_DC+goal][1]
                        grade_list.append(round(belief_grade,4))

            ''' Selection of the best action '''
            # Check if several actions have the same grade
            max_best_action = max(grade_list)
            count = 0
            count_max_list = []
            for item in grade_list:
                if item == max_best_action:
                    count_max_list.append(count)  # storing the indexes of the grades
                count += 1

            if len(count_max_list) > 1: # if there are several grades at the max level, then choose randomly
                best_action_index = random.choice(count_max_list)
            else:  # if not, the best grade is the maximum
                best_action_index = grade_list.index(max(grade_list))

            # calculating the best action - 0,len_PC is likelihood, len_PC,2*len_PC is belief, 2*len_PC,3*len_PC is goal
            best_action = best_action_index - (3*len_PC) * int(best_action_index/(3*len_PC))

            ''' Implementation of the best action '''
            
            for agent in self.model.schedule.agent_buffer(shuffled=True):
                # make sure to select the right agent onto which the actions is performed
                if isinstance(agent, ActiveAgent) and agent == grade_list_agents[int(best_action_index/(3*len_PC))]:

                    _unique_id = agent.unique_id

                    # framing influence action
                    if best_action < len_PC:
                        PF_targ = best_action
                        agent.policytree[_unique_id][0][self.selected_PF][PF_targ] += (self.policytree[self.unique_id][0][self.selected_PF][PF_targ] - agent.policytree[_unique_id][0][self.selected_PF][PF_targ])  * self.resources * weightResources * weightAction
                        agent.policytree[_unique_id][0][self.selected_PF][PF_targ] = round(agent.policytree[_unique_id][0][self.selected_PF][PF_targ], 4)

                    # belief influence action
                    if best_action >= len_PC and best_action < 2*len_PC:
                        PC_targ = best_action - len_PC
                        agent.issuetree[_unique_id][len_DC+PC_targ][0] += (self.issuetree[self.unique_id][len_DC+PC_targ][0] - agent.issuetree[_unique_id][len_DC+PC_targ][0])  * self.resources * weightResources * weightAction
                        agent.issuetree[_unique_id][len_DC+PC_targ][0] = round(agent.issuetree[_unique_id][len_DC+PC_targ][0], 4)

                    # goal influence action
                    if best_action >= 2*len_PC:
                        PC_targ = best_action - 2*len_PC
                        agent.issuetree[_unique_id][len_DC+PC_targ][1] += (self.issuetree[self.unique_id][len_DC+PC_targ][1] - agent.issuetree[_unique_id][len_DC+PC_targ][1])  * self.resources * weightResources * weightAction
                        agent.issuetree[_unique_id][len_DC+PC_targ][1] = round(agent.issuetree[_unique_id][len_DC+PC_targ][1], 4)

                    # updating the conflict level after each action
                    self.model.conflictLevel_update_policy_PF(self, agent)
            
            _iter += 1
            resources_action -= self.resources * weightResources

    def action_PF_issue(self, action_param):

        '''
        The action function for issue focused agents in the policy formulation
        ===========================

        This function is used to calculate the likelihood of an agent performing an action and apply the selected action. This is for the issue focused agents in the policy formulation. The actions allowed are:
        - (Framing 'fra') - Influence on the causal relations above the selected secondary issue
        - (Direct goal influence 'dgoa') - Influence on the goals of the selected secondary issue
        - (Direct belief influence 'dbel') - Influence on the beliefs of the selected secondary issue

        The action with the highest likelihood is selected.

        Note: Full knolwedge is used in this function

        '''

        len_DC = self.model.len_DC
        len_PC = self.model.len_PC
        len_S = self.model.len_S
        issue_number = len_DC + len_PC + len_S


        weightAction = action_param [0]
        weightResources = action_param[1]  # defines how many of the resources are spent per action
        weightBonusInit = action_param[2]
        resources_action = self.resources

        # selection of the causal relation of interest
        cr_selec = []
        # only consider the causal relations related to the issue selected by the agent
        for cr_choice in range(len_PC):
            cr_selec.append(len_DC + len_PC + len_S + len_DC*len_PC + self.selected_S + cr_choice*len_S)

        _iter = 0
        while resources_action > 0.001:

            ''' Calculation of the likelihood '''
            grade_list = []
            grade_list_agents = []
            for agent in self.model.schedule.agent_buffer(shuffled=True):
                if isinstance(agent, ActiveAgent) and agent != self:

                    if agent.agent_type == 'policymaker':
                        weightBonus = weightBonusInit
                    else:
                        weightBonus = 1

                    _unique_id = agent.unique_id
                    grade_list_agents.append(agent)
                            
                    # grading all framing likelihood actions:
                    for cr in cr_selec:
                        cr_grade = self.conflictLevelIssue[_unique_id][cr][0] * weightBonus
                        grade_list.append(round(cr_grade,4)) 

                    # grading belief likelihood change
                    belief_grade = self.conflictLevelIssue[_unique_id][len_DC+len_PC+self.selected_S][0] * weightBonus
                    grade_list.append(round(belief_grade,4))

                    # grading aim likelihood change
                    goal_grade = self.conflictLevelIssue[_unique_id][len_DC+len_PC+self.selected_S][1] * weightBonus
                    grade_list.append(round(goal_grade,4))

            ''' Selection of the best action '''
            # Check if several actions have the same grade
            max_best_action = max(grade_list)
            count = 0
            count_max_list = []
            for item in grade_list:
                if item == max_best_action:
                    count_max_list.append(count)  # storing the indexes of the grades
                count += 1

            if len(count_max_list) > 1: # if there are several grades at the max level, then choose randomly
                best_action_index = random.choice(count_max_list)
            else:  # if not, the best grade is the maximum
                best_action_index = grade_list.index(max(grade_list))

            # calculating the best action - 0,len(cr_selec) is cr, len(cr_selec)+1 is belief, len(cr_selec)+2 is goal
            best_action = best_action_index - (len(cr_selec) + 2) * int(best_action_index/(len(cr_selec) + 2))

            ''' Implementation of the best action '''
            
            for agent in self.model.schedule.agent_buffer(shuffled=True):
                # make sure to select the right agent onto which the actions is performed
                if isinstance(agent, ActiveAgent) and agent == grade_list_agents[int(best_action_index/(len(cr_selec) + 2))]:

                    _unique_id = agent.unique_id

                    # framing influence action
                    if best_action < len(cr_selec):
                        cr_act = cr_selec[best_action]  # defining the causal relation
                        agent.issuetree[_unique_id][cr_act][0] += (self.issuetree[self.unique_id][cr_act][0] - agent.issuetree[_unique_id][cr_act][0])  * self.resources * weightResources * weightAction
                        agent.issuetree[_unique_id][cr_act][0] = round(agent.issuetree[_unique_id][cr_act][0], 4)

                    # belief influence action
                    if best_action == len(cr_selec):
                        agent.issuetree[_unique_id][len_DC+len_PC+self.selected_S][0] += (self.issuetree[self.unique_id][len_DC+len_PC+self.selected_S][0] - agent.issuetree[_unique_id][len_DC+len_PC+self.selected_S][0])  * self.resources * weightResources * weightAction
                        agent.issuetree[_unique_id][len_DC+len_PC+self.selected_S][0] = round(agent.issuetree[_unique_id][len_DC+len_PC+self.selected_S][0], 4)

                    # goal influence action
                    if best_action == len(cr_selec) + 1:
                        agent.issuetree[_unique_id][len_DC+len_PC+self.selected_S][1] += (self.issuetree[self.unique_id][len_DC+len_PC+self.selected_S][1] - agent.issuetree[_unique_id][len_DC+len_PC+self.selected_S][1])  * self.resources * weightResources * weightAction
                        agent.issuetree[_unique_id][len_DC+len_PC+self.selected_S][1] = round(agent.issuetree[_unique_id][len_DC+len_PC+self.selected_S][1], 4)

                    # updating the conflict level after each action
                    self.model.conflictLevel_update_issue(self, agent)
            
            _iter += 1
            resources_action -= self.resources * weightResources

    def action_PF_policy(self, action_param):

        '''
        The action function for policy focused agents in the policy formulation
        ===========================

        This function is used to calculate the likelihood of an agent performing an action and apply the selected action. This is for the policy focused agents in the policy formulation. The actions allowed are:
        - (Impact influence 'imp') - Influence on the perceived impact of the policy instruments
        - (Goal influence 'goa') - Influence on the goals of the associated secondary issues
        - (Belief influence 'bel') - Influence on the beliefs of the associated secondary issues

        The action with the highest likelihood is selected.

        Note: Full knolwedge is used in this function

        '''

        len_PF = self.model.len_PC
        len_DC = self.model.len_DC
        len_PC = self.model.len_PC
        len_S = self.model.len_S
        issue_number = len_DC + len_PC + len_S

        weightAction = action_param [0]
        weightResources = action_param[1]  # defines how many of the resources are spent per action
        weightBonusInit = action_param[2]
        resources_action = self.resources

        _iter = 0
        while resources_action > 0.001:

            ''' Calculation of the likelihood '''
            grade_list = []
            grade_list_agents = []
            for agent in self.model.schedule.agent_buffer(shuffled=True):
                if isinstance(agent, ActiveAgent) and agent != self:

                    if agent.agent_type == 'policymaker':
                        weightBonus = weightBonusInit
                    else:
                        weightBonus = 1

                    _unique_id = agent.unique_id
                    grade_list_agents.append(agent)
                            
                    # grading all framing likelihood actions:
                    for imp in range(len_S):
                        imp_grade = self.conflictLevelPolicy[_unique_id][1][self.selected_PI][imp] * weightBonus
                        grade_list.append(round(imp_grade,4)) 

                    # grading belief likelihood change
                    for belief in range(len_S):
                        belief_grade = self.conflictLevelIssue[_unique_id][len_DC+len_PC+belief][0] * weightBonus
                        grade_list.append(round(belief_grade,4))

                    # grading aim likelihood change
                    for goal in range(len_S):
                        goal_grade = self.conflictLevelIssue[_unique_id][len_DC+len_PC+goal][1] * weightBonus
                        grade_list.append(round(belief_grade,4))

            ''' Selection of the best action '''
            # Check if several actions have the same grade
            max_best_action = max(grade_list)
            count = 0
            count_max_list = []
            for item in grade_list:
                if item == max_best_action:
                    count_max_list.append(count)  # storing the indexes of the grades
                count += 1

            if len(count_max_list) > 1: # if there are several grades at the max level, then choose randomly
                best_action_index = random.choice(count_max_list)
            else:  # if not, the best grade is the maximum
                best_action_index = grade_list.index(max(grade_list))

            # calculating the best action - 0,len_S is impact, len_S,2*len_S is belief, 2*len_S,3*len_S is goal
            best_action = best_action_index - (3*len_S) * int(best_action_index/(3*len_S))

            ''' Implementation of the best action '''
            
            for agent in self.model.schedule.agent_buffer(shuffled=True):
                # make sure to select the right agent onto which the actions is performed
                if isinstance(agent, ActiveAgent) and agent == grade_list_agents[int(best_action_index/(3*len_S))]:

                    _unique_id = agent.unique_id

                    # framing influence action
                    if best_action < len_S:
                        PI_targ = best_action
                        agent.policytree[_unique_id][1][self.selected_PI][PI_targ] += (self.policytree[self.unique_id][1][self.selected_PI][PI_targ] - agent.policytree[_unique_id][1][self.selected_PI][PI_targ])  * self.resources * weightResources * weightAction
                        agent.policytree[_unique_id][1][self.selected_PI][PI_targ] = round(agent.policytree[_unique_id][1][self.selected_PI][PI_targ], 4)

                    # belief influence action
                    if best_action >= len_S and best_action < 2*len_S:
                        S_targ = best_action - len_S
                        agent.issuetree[_unique_id][len_DC+len_PC+S_targ][0] += (self.issuetree[self.unique_id][len_DC+len_PC+S_targ][0] - agent.issuetree[_unique_id][len_DC+len_PC+S_targ][0])  * self.resources * weightResources * weightAction
                        agent.issuetree[_unique_id][len_DC+len_PC+S_targ][0] = round(agent.issuetree[_unique_id][len_DC+len_PC+S_targ][0], 4)

                    # goal influence action
                    if best_action >= 2*len_S:
                        S_targ = best_action - 2*len_S
                        agent.issuetree[_unique_id][len_DC+len_PC+S_targ][1] += (self.issuetree[self.unique_id][len_DC+len_PC+S_targ][1] - agent.issuetree[_unique_id][len_DC+len_PC+S_targ][1])  * self.resources * weightResources * weightAction
                        agent.issuetree[_unique_id][len_DC+len_PC+S_targ][1] = round(agent.issuetree[_unique_id][len_DC+len_PC+S_targ][1], 4)

                    # updating the conflict level after each action
                    self.model.conflictLevel_update_policy_PI(self, agent)
            
            _iter += 1
            resources_action -= self.resources * weightResources


class ElectorateAgent(Agent):
    '''
    Electorate agents.
    '''
    def __init__(self, pos, unique_id, model, affiliation, issuetree_elec, representativeness):
        '''
         Create a new Electorate agent.
         Args:
            unique_id: Unique identifier for the agent.
            x, y: Agent initial location.
            unique_id: 
        '''
        super().__init__(pos, model)
        self.pos = pos  # defines the position of the agent on the grid
        self.unique_id = unique_id  # unique_id of the agent used for algorithmic reasons
        self.affiliation = affiliation  # political affiliation affecting agent interactions
        self.issuetree_elec = issuetree_elec  # issue tree of the agent (including partial issue of other agents)
        self.representativeness = representativeness

    def electorate_influence(self, w_el_influence):

        '''
        Function that defines the electorate influence on the policy makers.
        This function is dependent on the electorate influence weight value which can be adjusted as a tuning parameter.
        '''

        len_DC = self.model.len_DC
        len_PC = self.model.len_PC
        len_S = self.model.len_S

        for agent in self.model.schedule.agent_buffer(shuffled=True):  
            if isinstance(agent, ActiveAgent) and agent.agent_type == 'policymaker' and agent.affiliation == self.affiliation:
                _unique_id = agent.unique_id
                for issue in range(len_DC+len_PC+len_S):
                    agent.issuetree[_unique_id][issue][1] += (self.issuetree_elec[issue] - agent.issuetree[_unique_id][issue][1]) * w_el_influence * abs(agent.issuetree[_unique_id][issue][1] - agent.issuetree[_unique_id][issue][0])

class TruthAgent(Agent):
    '''
    Truth agents.
    '''
    def __init__(self, pos, model, issuetree_truth, policytree_truth):
        '''
         Create a new Truth agent.
         Args:
            unique_id: Unique identifier for the agent.
            x, y: Agent initial location.
        '''
        super().__init__(pos, model)
        self.pos = pos  # defines the position of the agent on the grid
        self.issuetree_truth = issuetree_truth  # issue tree of the agent (including partial issue of other agents)
        self.policytree_truth = policytree_truth
    