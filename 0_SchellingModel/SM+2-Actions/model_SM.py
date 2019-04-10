from mesa import Model, Agent
from mesa.time import RandomActivation
from mesa.space import SingleGrid
from mesa.datacollection import DataCollector
import numpy as np

from collections import defaultdict

from model_SM_agents_initialisation import init_active_agents, init_electorate_agents, init_truth_agent
from model_SM_agents import ActiveAgent, ElectorateAgent, TruthAgent
from model_module_interface import policy_instrument_input, issue_tree_input


# Data collector function

def get_agents_attributes(model):
	
	agent_attributes = []
	for agent in model.schedule.agent_buffer(shuffled=False):
		if isinstance(agent, ActiveAgent):
			_unique_id = agent.unique_id
			agent_attributes.append([_unique_id, agent.agent_type, agent.affiliation, agent.selected_PC, agent.selected_PF, agent.selected_S, agent.selected_PI, agent.issuetree[_unique_id], agent.policytree[_unique_id]])

	return agent_attributes

def get_problem_policy_chosen(model):

	return [model.agenda_PC, model.agenda_PF, model.policy_implemented_number]

class PolicyEmergenceSM(Model):

	'''
	Simplest Model for the policy emergence model.
	'''

	def __init__(self, SM_inputs, height=20, width=20):

		self.height = height
		self.width = width

		self.SM_inputs = SM_inputs
		self.conflictLevel_coefficient = SM_inputs[9]  # conflict level coefficients

		self.stepCount = 0
		self.agenda_PC = None
		self.agenda_PF = None
		self.policy_implemented = None
		self.policy_implemented_number = None
		self.policy_formulation_run = False  # True if an agenda is found

		self.w_el_influence = 0.05  # electorate influence weight

		self.schedule = RandomActivation(self)
		self.grid = SingleGrid(height, width, torus=True)

		# creation of the datacollector vector
		self.datacollector = DataCollector(
			# Model-level variables
			model_reporters =  {
				"step": "stepCount",
				"AS_PF": get_problem_policy_chosen,
				"agent_attributes": get_agents_attributes},
			# Agent-level variables
			agent_reporters = {
				"x": lambda a: a.pos[0],
				"y": lambda a: a.pos[1],
				"Agent type": lambda a:type(a), 
				"Issuetree": lambda a: getattr(a, 'issuetree', [None])[a.unique_id if isinstance(a, ActiveAgent) else 0]}
			)

		# , "agenda_PC":"agenda_PC", "agenda_PF":"agenda_PF", "policy_implemented": "policy_implemented"

		# "x": lambda a: a.pos[0], "y": lambda a: a.pos[1]
		# "z": lambda a:a.issuetree

		# belief tree properties
		self.len_S, self.len_PC, self.len_DC, self.len_CR = issue_tree_input(self)
		# print(self.len_S, self.len_PC, self.len_DC, self.len_CR)

		# issue tree properties
		self.policy_instruments, self.len_ins_1, self.len_ins_2, self.len_ins_all, self.PF_indices = policy_instrument_input(self, self.len_PC)

		# Set up active agents
		init_active_agents(self, self.len_S, self.len_PC, self.len_DC, self.len_CR, self.len_PC, self.len_ins_1, self.len_ins_2, self.len_ins_all, self.SM_inputs)

		# Set up passive agents
		init_electorate_agents(self, self.len_S, self.len_PC, self.len_DC, self.SM_inputs)

		# Set up truth agent
		init_truth_agent(self, self.len_S, self.len_PC, self.len_DC, self.len_ins_1, self.len_ins_2, self.len_ins_all)
		# the issue tree will need to be updated at a later stage witht he values from the system/policy context

		# print("Schedule has : ", len(self.schedule.agents), " agents.")
		# print(self.schedule.agents)
		# print(" ")

		# for agent in self.schedule.agent_buffer(shuffled=False):
		# 	print(' ')
		# 	print(agent)
		# 	print(type(agent))
		# 	if isinstance(agent, ActiveAgent):
		# 		print(agent.unique_id, " ", agent.pos, " ", agent.agent_type, " ", agent.resources, " ", agent.affiliation, " ", agent.issuetree[agent.unique_id], " ", agent.policytree[agent.unique_id][0])
		# 	if isinstance(agent, ElectorateAgent):
		# 		print(agent.unique_id, " ", agent.pos, " ", agent.affiliation, " ", agent.issuetree)
		# 	if isinstance(agent, TruthAgent):
		# 		print(agent.pos, " ", agent.issuetree)

		self.running = True
		self.numberOfAgents = self.schedule.get_agent_count()
		self.datacollector.collect(self)

	def step(self, SM_version, KPIs):
		print(" ")
		print("Step +1 - Policy emergence model")
		print("Step count: ", self.stepCount)

		'''
		Main steps of the Simplest Model for policy emergence:
		0. Module interface - Input
			Obtention of the beliefs from the system/policy context
			!! This is to be implemented at a later stage
		1. Agenda setting step
		2. Policy formulation step
		3. Module interface - Output
			Implementation of the policy instrument selected
		'''

		# saving the attributes
		self.KPIs = KPIs

		# 0.
		self.module_interface_input(self.KPIs)  # transfer of the states
		if SM_version >= 1: # SM+1 and higher
			self.electorate_influence(self.w_el_influence)  # electorate influence action		

		# 1.
		self.agenda_setting()

		# 2.
		if self.policy_formulation_run:  # making sure first that an agenda has been created
			self.policy_formulation()
		else:  # otherwise, the status quo remains
			self.policy_implemented = self.policy_instruments[-1]

		# 3.
		# self.module_interface_output()

		# end of step actions:
		# iterate the steps counter
		self.stepCount += 1

		# collect data
		self.datacollector.collect(self)

		print("step ends")
		print(" ")

		# print(self.datacollector.get_agent_vars_dataframe())
		print(self.datacollector.get_model_vars_dataframe())

		return self.policy_implemented

	def module_interface_input(self, KPIs):

		'''
		The module interface input step consists of actions related to the module interface and the policy emergence model

		'''

		# selection of the Truth agent policy tree and issue tree
		for agent in self.schedule.agent_buffer(shuffled=True):
			if isinstance(agent, TruthAgent):
				truth_policytree = agent.policytree_truth
				for issue in range(self.len_DC+self.len_PC+self.len_S):
					agent.issuetree_truth[issue] = KPIs[issue]
				truth_issuetree = agent.issuetree_truth

		# transferring policy impact to active agents
		for agent in self.schedule.agent_buffer(shuffled=True):
			if isinstance(agent, ActiveAgent):
				# replacing the policy family likelihoods
				for PFj in range(self.len_PC):
					for PFij in range(self.len_PC):
						# agent.policytree[agent.unique_id][PFj][PFij] = truth_policytree[PFj][PFij]
						agent.policytree[agent.unique_id][0][PFj][PFij] = truth_policytree[PFj][PFij]

				# replacing the policy instruments impacts
				for insj in range(self.len_ins_1 + self.len_ins_2 + self.len_ins_all):
					# agent.policytree[agent.unique_id][self.len_PC+insj][0:self.len_S] = truth_policytree[self.len_PC+insj]
					agent.policytree[agent.unique_id][1][insj][0:self.len_S] = truth_policytree[self.len_PC+insj]

				# replacing the issue beliefs from the KPIs
				for issue in range(self.len_DC+self.len_PC+self.len_S):
					agent.issuetree[agent.unique_id][issue][0] = truth_issuetree[issue]
				agent.preference_update(agent, agent.unique_id)

		# updating conflict levels
		for agent in self.schedule.agent_buffer(shuffled=False):
			for who in self.schedule.agent_buffer(shuffled=False):
				if isinstance(agent, ActiveAgent) and isinstance(who, ActiveAgent):
					agent.conflictLevel_update(agent, who)

	def electorate_influence(self, w_el_influence):

		'''
		This function calls the influence actions in the electorate agent class

		'''

		for agent in self.schedule.agent_buffer(shuffled=True):  
			if isinstance(agent, ElectorateAgent):
				agent.electorate_influence(w_el_influence)

	def agenda_setting(self):

		'''
		The agenda setting step is the first step in the policy process conceptualised in this model. The steps are given as follows:
		1. Active agents policy core issue selection
		2. Active agents policy family selection
		3. Active agents actions [to be detailed later]
		4. Active agents policy core issue selection update
		5. Active agents policy family selection update
		6. Agenda selection
		'''

		# 1. & 2.
		for agent in self.schedule.agent_buffer(shuffled=False):
			if isinstance(agent, ActiveAgent):  # considering only active agents
				agent.selection_PC()
				agent.selection_PF()
				# print("PC and PF selected for  agent", agent.unique_id, ": ", agent.selected_PC, agent.selected_PF)

		# 3.

		# 4. & 5.
		for agent in self.schedule.agent_buffer(shuffled=False):
			if isinstance(agent, ActiveAgent):  # considering only active agents
				agent.selection_PC()
				agent.selection_PF()

		# 6. 
		# All active agents considered
		selected_PC_list = []
		selected_PF_list = []
		number_ActiveAgents = 0
		for agent in self.schedule.agent_buffer(shuffled=False):
			if isinstance(agent, ActiveAgent):  # considering only policy makers
				selected_PC_list.append(agent.selected_PC)
				selected_PF_list.append(agent.selected_PF)
				number_ActiveAgents += 1

		# finding the most common policy core issue and its frequency
		d = defaultdict(int)
		for i in selected_PC_list:
			d[i] += 1
		result = max(d.items(), key=lambda x: x[1])
		agenda_PC_temp = result[0]
		agenda_PC_temp_frequency = result[1]

		# finding the most common policy family issue and its frequency
		d = defaultdict(int)
		for i in selected_PF_list:
			d[i] += 1
		result = max(d.items(), key=lambda x: x[1])
		agenda_PF_temp = result[0]
		agenda_PF_temp_frequency = result[1]

		# checking for majority
		if agenda_PC_temp_frequency > int(number_ActiveAgents/2) and agenda_PF_temp_frequency > int(number_ActiveAgents/2):
			self.agenda_PC = agenda_PC_temp
			self.agenda_PF = agenda_PF_temp
			self.policy_formulation_run = True
			print("The agenda consists of PC", self.agenda_PC, " and PF", self.agenda_PF, ".")
		else:
			self.policy_formulation_run = False
			print("No agenda was formed, moving to the next step.")

	def policy_formulation(self):

		'''
		The policy formulation step is the second step in the policy process conceptualised in this model. The steps are given as follows:
		0. Detailing of policy instruments that can be considered
		1. Active agents deep core issue selection
		2. Active agents policy instrument selection
		3. Active agents actions [to be detailed later]
		4. Active agents policy instrument selection update
		5. Policy instrument selection

		NOTE: THIS CODE DOESNT CONSIDER MAJORITY WHEN MORE THAN THREE POLICY MAKERS ARE INCLUDED, IT CONSIDERS THE MAXIMUM. THIS NEEDS TO BE ADAPTED TO CONSIDER 50% OR MORE!
		'''

		print("Policy formulation being introduced")

		# 0.
		possible_PI = self.PF_indices[self.agenda_PF]

		# 1. & 2.
		for agent in self.schedule.agent_buffer(shuffled=False):
			if isinstance(agent, ActiveAgent):  # considering only active agents
				agent.selection_S()
				self.preference_update_PI(agent, agent.unique_id)  # update of the preferences
				agent.selection_PI()

		# updating conflict levels
		for agent in self.schedule.agent_buffer(shuffled=False):
			for who in self.schedule.agent_buffer(shuffled=False):
				if isinstance(agent, ActiveAgent) and isinstance(who, ActiveAgent):
					self.conflictLevel_update_policy_PI(agent, who)

		# 3.

		# 4. & 5.
		for agent in self.schedule.agent_buffer(shuffled=False):
			if isinstance(agent, ActiveAgent):  # considering only active agents
				self.preference_update_PI(agent, agent.unique_id)  # update of the preferences
				agent.selection_PI()

		# 6. 
		# Only policy makers considered
		selected_PI_list = []
		number_PMs = 0
		for agent in self.schedule.agent_buffer(shuffled=False):
			if isinstance(agent, ActiveAgent) and agent.agent_type == 'policymaker':  # considering only policy makers
				selected_PI_list.append(agent.selected_PI)
				number_PMs += 1

		# finding the most common secondary issue and its frequency
		d = defaultdict(int)
		for i in selected_PI_list:
			d[i] += 1
		result = max(d.items(), key=lambda x: x[1])
		self.policy_implemented_number = result[0]
		policy_implemented_number_frequency = result[1]

		# check for the majority and implemented if satisfied
		if policy_implemented_number_frequency > int(number_PMs/2):
			print("The policy instrument selected is policy instrument ", self.policy_implemented_number, ".")
			self.policy_implemented = self.policy_instruments[self.policy_implemented_number]
		else:
			print("No consensus on a policy instrument.")
			self.policy_implemented = self.policy_instruments[-1] # selecting last policy instrument which is the no instrument policy instrument

	def module_interface_output(self):

		print("Module interface output not introduced yet")

	def preference_update_DC(self, agent, who):

		"""
		The preference update function (DC)
		===========================

		This function is used to update the preferences of the deep core issues of agents in their
		respective belief trees.

		agent - this is the owner of the belief tree
		who - this is the part of the belieftree that is considered - agent.unique_id should be used for this - this is done to also include partial knowledge preference calculation

		"""	

		len_DC = self.len_DC
		len_PC = self.len_PC
		len_S = self.len_S

		#####
		# 1.5.1. Preference calculation for the deep core issues

		# 1.5.1.1. Calculation of the denominator
		PC_denominator = 0
		for h in range(len_DC):
			if agent.issuetree[who][h][1] == None or agent.issuetree[who][h][0] == None:
				PC_denominator = 0
			else:
				PC_denominator = PC_denominator + abs(agent.issuetree[who][h][1] - agent.issuetree[who][h][0])
		# print('The denominator is given by: ' + str(PC_denominator))

		# 1.5.1.2. Selection of the numerator and calculation of the preference
		for i in range(len_DC):
			# There are rare occasions where the denominator could be 0
			if PC_denominator != 0:
				agent.issuetree[who][i][2] = abs(agent.issuetree[who][i][1] - agent.issuetree[who][i][0]) / PC_denominator
			else:
				agent.issuetree[who][i][2] = 0

	def preference_update_PC(self, agent, who):

		"""
		The preference update function (PC)
		===========================

		This function is used to update the preferences of the policy core issues of agents in their
		respective belief trees.

		agent - this is the owner of the belief tree
		who - this is the part of the belieftree that is considered - agent.unique_id should be used for this - this is done to also include partial knowledge preference calculation

		"""	

		len_DC = self.len_DC
		len_PC = self.len_PC
		len_S = self.len_S

		#####	
		# 1.5.2 Preference calculation for the policy core issues
		PC_denominator = 0
		# 1.5.2.1. Calculation of the denominator
		for j in range(len_PC):
			# print('Selection PC' + str(j+1))
			# print('State of the PC' + str(j+1) + ': ' + str(agent.issuetree[0][len_DC + j][0])) # the state printed
			# Selecting the causal relations starting from PC
			for k in range(len_DC):
				# Contingency for partial knowledge issues
				if agent.issuetree[who][k][1] == None or agent.issuetree[who][k][0] == None or agent.issuetree[who][len_DC+len_PC+len_S+j+(k*len_PC)][0] == None:
					PC_denominator += 0
				else:
					# print('Causal Relation PC' + str(j+1) + ' - PC' + str(k+1) + ': ' + str(agent.issuetree[0][len_DC+len_PC+len_S+j+(k*len_PC)][1]))
					# print('Gap of PC' + str(k+1) + ': ' + str((agent.issuetree[0][k][1] - agent.issuetree[0][k][0])))
					# Check if causal relation and gap are both positive of both negative
					# print('agent.issuetree[' + str(who) + '][' + str(len_DC+len_PC+len_S+j+(k*len_PC)) + '][0]: ' + str(agent.issuetree[who][len_DC+len_PC+len_S+j+(k*len_PC)][0]))
					if (agent.issuetree[who][len_DC+len_PC+len_S+j+(k*len_PC)][0] < 0 and (agent.issuetree[who][k][1] - agent.issuetree[who][k][0]) < 0) or (agent.issuetree[who][len_DC+len_PC+len_S+j+(k*len_PC)][0] > 0 and (agent.issuetree[who][k][1] - agent.issuetree[who][k][0]) > 0):
						PC_denominator = PC_denominator + abs(agent.issuetree[who][len_DC+len_PC+len_S+j+(k*len_PC)][0]*(agent.issuetree[who][k][1] - agent.issuetree[who][k][0]))
						# print('This is the PC numerator: ' + str(PC_denominator))
					else:
						PC_denominator = PC_denominator	

		# 1.5.2.2. Addition of the gaps of the associated mid-level issues
		for i in range(len_PC):
			# Contingency for partial knowledge issues
			if agent.issuetree[who][len_DC + i][1] == None or agent.issuetree[who][len_DC + i][0] == None:
				PC_denominator = PC_denominator
			else:
				# print('This is the gap for the PC' + str(i+1) + ': ' + str(agent.issuetree[0][len_DC + i][1] - agent.issuetree[0][len_DC + i][0]))
				PC_denominator += abs(agent.issuetree[who][len_DC + i][1] - agent.issuetree[who][len_DC + i][0])
		# print('This is the S denominator: ' + str(PC_denominator))
		
		# 1.5.2.3 Calculation the numerator and the preference
		# Select one by one the PC
		for j in range(len_PC):

			# 1.5.2.3.1. Calculation of the right side of the numerator
			PC_numerator = 0
			# print('Selection PC' + str(j+1))
			# print('State of the PC' + str(j+1) + ': ' + str(agent.issuetree[0][len_DC + j][0])) # the state printed
			# Selecting the causal relations starting from DC
			for k in range(len_DC):
				# Contingency for partial knowledge issues
				if agent.issuetree[who][k][1] == None or agent.issuetree[who][k][0] == None or agent.issuetree[who][len_DC+len_PC+len_S+j+(k*len_PC)][0] == None:
					PC_numerator += 0
				else:
					# print('Causal Relation PC' + str(j+1) + ' - DC' + str(k+1) + ': ' + str(agent.issuetree[0][len_DC+len_PC+len_S+j+(k*len_PC)][1]))
					# print('Gap of DC' + str(k+1) + ': ' + str((agent.issuetree[0][k][1] - agent.issuetree[0][k][0])))
					# Check if causal relation and gap are both positive of both negative
					if (agent.issuetree[who][len_DC+len_PC+len_S+j+(k*len_PC)][0] < 0 and (agent.issuetree[who][k][1] - agent.issuetree[who][k][0]) < 0) or (agent.issuetree[who][len_DC+len_PC+len_S+j+(k*len_PC)][0] > 0 and (agent.issuetree[who][k][1] - agent.issuetree[who][k][0]) > 0):
						PC_numerator = PC_numerator + abs(agent.issuetree[who][len_DC+len_PC+len_S+j+(k*len_PC)][0]*(agent.issuetree[who][k][1] - agent.issuetree[who][k][0]))
						# print('This is the PC numerator: ' + str(PC_numerator))
					else:
						PC_numerator = PC_numerator	

			# 1.5.2.3.2. Addition of the gap to the numerator
			# Contingency for partial knowledge issues
			if agent.issuetree[who][len_DC + j][1] == None or agent.issuetree[who][len_DC + j][0] == None:
				PC_numerator += 0
			else:
				# print('This is the gap for the PC' + str(j+1) + ': ' + str(agent.issuetree[0][len_DC + j][1] - agent.issuetree[0][len_DC + j][0]))
				PC_numerator += abs(agent.issuetree[who][len_DC + j][1] - agent.issuetree[who][len_DC + j][0])
			# print('The numerator is equal to: ' + str(PC_numerator))
			# print('The denominator is equal to: ' + str(PC_denominator))

			# 1.5.2.3.3. Calculation of the preference
			if PC_denominator != 0:
				agent.issuetree[who][len_DC+j][2] = round(PC_numerator/PC_denominator,3) 
			# print('The new preference of the policy core PC' + str(j+1) + ' is: ' + str(agent.issuetree[0][len_DC+j][2]))
			else:
				agent.issuetree[who][len_DC+j][2] = 0

	def preference_update_S(self, agent, who):

		"""
		The preference update function (S)
		===========================

		This function is used to update the preferences of secondary issues the agents in their
		respective belief trees.

		agent - this is the owner of the belief tree
		who - this is the part of the belieftree that is considered - agent.unique_id should be used for this - this is done to also include partial knowledge preference calculation

		"""	

		len_DC = self.len_DC
		len_PC = self.len_PC
		len_S = self.len_S

		#####	
		# 1.5.3 Preference calculation for the secondary issues
		S_denominator = 0
		# 1.5.2.1. Calculation of the denominator
		for j in range(len_S):
			# print('Selection S' + str(j+1))
			# print('State of the S' + str(j+1) + ': ' + str(agent.issuetree[0][len_DC + len_PC + j][0])) # the state printed
			# Selecting the causal relations starting from S
			for k in range(len_PC):
				# Contingency for partial knowledge issues
				if agent.issuetree[who][len_DC + k][1] == None or agent.issuetree[who][len_DC + k][0] == None or agent.issuetree[who][len_DC+len_PC+len_S+len_DC*len_PC+j+(k*len_S)][0] == None:
					S_denominator += 0
				else:
					# print('Causal Relation S' + str(j+1) + ' - PC' + str(k+1) + ': ' + str(agent.issuetree[who][len_DC+len_PC+len_S+len_DC*len_PC+j+(k*len_S)][0]))
					# print('Gap of PC' + str(k+1) + ': ' + str((agent.issuetree[who][len_DC+k][1] - agent.issuetree[who][len_DC+k][0])))
					# Check if causal relation and gap are both positive of both negative
					# print('agent.issuetree[' + str(who) + '][' + str(len_DC+len_PC+len_S+len_DC*len_PC+j+(k*len_S)) + '][0]: ' + str(agent.issuetree[who][len_DC+len_PC+len_S+len_DC*len_PC+j+(k*len_S)][0]))
					if (agent.issuetree[who][len_DC+len_PC+len_S+len_DC*len_PC+j+(k*len_S)][0] < 0 and (agent.issuetree[who][len_DC+k][1] - agent.issuetree[who][len_DC+k][0]) < 0) or (agent.issuetree[who][len_DC+len_PC+len_S+len_DC*len_PC+j+(k*len_S)][0] > 0 and (agent.issuetree[who][len_DC+k][1] - agent.issuetree[who][len_DC+k][0]) > 0):
						S_denominator += abs(agent.issuetree[who][len_DC+len_PC+len_S+len_DC*len_PC+j+(k*len_S)][0]*(agent.issuetree[who][len_DC+k][1] - agent.issuetree[who][len_DC+k][0]))
						# print('This is the PC numerator: ' + str(S_denominator))
					else:
						S_denominator = S_denominator	

		# 1.5.2.2. Addition of the gaps of the associated secondary issues
		for j in range(len_S):
			# Contingency for partial knowledge issues
			if agent.issuetree[who][len_DC+len_PC+j][1] == None or agent.issuetree[who][len_DC+len_PC+j][0] == None:
				S_denominator = S_denominator
			else:
				# print('This is the gap for the PC' + str(i+1) + ': ' + str(agent.issuetree[0][len_DC + len_PC + i][1] - agent.issuetree[0][len_DC + len_PC + i][0]))
				S_denominator += abs(agent.issuetree[who][len_DC+len_PC+j][1] - agent.issuetree[who][len_DC+len_PC+j][0])
		# print('This is the PC denominator: ' + str(S_denominator))
		
		# 1.5.2.3 Calculation the numerator and the preference
		# Select one by one the S
		for j in range(len_S):

			# 1.5.2.3.1. Calculation of the right side of the numerator
			S_numerator = 0
			# print('Selection S' + str(j+1))
			# print('State of the S' + str(j+1) + ': ' + str(agent.issuetree[who][len_DC + len_PC + j][0])) # the state printed
			# Selecting the causal relations starting from PC
			for k in range(len_PC):
				# Contingency for partial knowledge issues
				if agent.issuetree[who][len_DC + k][1] == None or agent.issuetree[who][len_DC + k][0] == None or agent.issuetree[who][len_DC+len_PC+len_S+len_DC*len_PC+j+(k*len_S)][0] == None:
					S_numerator = 0
				else:
					# print('Causal Relation S' + str(j+1) + ' - PC' + str(k+1) + ': ' + str(agent.issuetree[who][len_DC+len_PC+len_S+len_DC*len_PC+j+(k*len_S)][0]))
					# print('Gap of PC' + str(k+1) + ': ' + str((agent.issuetree[who][len_DC + k][1] - agent.issuetree[who][len_DC + k][0])))
					# Check if causal relation and gap are both positive of both negative
					if (agent.issuetree[who][len_DC+len_PC+len_S+len_DC*len_PC+j+(k*len_S)][0] < 0 and (agent.issuetree[who][len_DC+k][1] - agent.issuetree[who][len_DC+k][0]) < 0) or (agent.issuetree[who][len_DC+len_PC+len_S+len_DC*len_PC+j+(k*len_S)][0] > 0 and (agent.issuetree[who][len_DC+k][1] - agent.issuetree[who][len_DC+k][0]) > 0):
						S_numerator += abs(agent.issuetree[who][len_DC+len_PC+len_S+len_DC*len_PC+j+(k*len_S)][0]*(agent.issuetree[who][len_DC+k][1] - agent.issuetree[who][len_DC+k][0]))
						# print('This is the PC numerator: ' + str(S_numerator))
					else:
						S_numerator = S_numerator

			# 1.5.2.3.2. Addition of the gap to the numerator
			# Contingency for partial knowledge issues
			if agent.issuetree[who][len_DC+len_PC+j][1] == None or agent.issuetree[who][len_DC+len_PC+j][0] == None:
				S_numerator += 0
			else:
				# print('This is the gap for the PC' + str(j+1) + ': ' + str(agent.issuetree[who][len_DC+len_PC+j][1] - agent.issuetree[who][len_DC+len_PC+j][0]))
				S_numerator += abs(agent.issuetree[who][len_DC+len_PC+j][1] - agent.issuetree[who][len_DC+len_PC+j][0])
			# print('The numerator is equal to: ' + str(S_numerator))
			# print('The denominator is equal to: ' + str(S_denominator))

			# 1.5.2.3.3. Calculation of the preference
			if S_denominator != 0:
				agent.issuetree[who][len_DC+len_PC+j][2] = round(S_numerator/S_denominator,3) 
			# print('The new preference of the policy core PC' + str(j+1) + ' is: ' + str(agent.issuetree[0][len_DC+j][2]))
			else:
				agent.issuetree[who][len_DC+len_PC+j][2] = 0

	def preference_update_PF(self, agent, who):

		"""
		The preference update function (PF)
		===========================

		This function is used to update the preferences of policy families the agents in their
		respective policy trees.

		agent - this is the owner of the policy tree
		who - this is the part of the policytree that is considered - agent.unique_id should be used for this - this is done to also include partial knowledge preference calculation

		"""	

		len_DC = self.len_DC
		len_PF = self.len_PC  # number of PC is always equal to number of PF
		len_PC = self.len_PC
		len_S = self.len_S

		# calculation of the preferences for all policy families
		# calculation of the denominator
		PF_denominator = 0
		# going through all policy families
		for PFj in range(len_PF):
			# going through all policy core issues
			for PCi in range(len_PC):
				gap = 0
				# print(" ")
				# print(PFj, PCi)
				# print(agent.policytree[who][0][PFj])
				# print(agent.policytree[who][0][PFj][PCi])
				# check if the likelihood is positive
				if agent.policytree[who][0][PFj][PCi] > 0:
					# calculating the gap
					# gap = agent.issuetree[who][len_DC+PCi][1] - agent.issuetree[who][len_DC+PCi][0]
					# print("Before: ", gap)
					gap = abs(agent.issuetree[who][len_DC+PCi][1] - (agent.issuetree[who][len_DC+PCi][0] * (1 + agent.policytree[who][0][PFj][PCi])))
					# print("After: ", gap)
				# check if the likelihood is negative
				if agent.policytree[who][0][PFj][PCi] < 0:
					# gap = agent.issuetree[who][len_DC+PCi][1] - agent.issuetree[who][len_DC+PCi][0]
					# print("Before: ", gap)
					# calculating the gap
					gap = abs(agent.issuetree[who][len_DC+PCi][1] - (agent.issuetree[who][len_DC+PCi][0] * abs(agent.policytree[who][0][PFj][PCi])))
					# print("After: ", gap)
				PF_denominator += round(gap,3)
				# print("PF_denominator: ", PF_denominator)

		# calculation of the numerator
		# going through all policy families
		for PFj in range(len_PF):
			PF_numerator = 0
			# going through all policy core issues
			for PCi in range(len_PC):
				gap = 0
				# print(" ")
				# print(PFj, PCi)
				# print(agent.policytree[who][0][PFj])
				# print(agent.policytree[who][0][PFj][PCi])
				# check if the likelihood is positive
				if agent.policytree[who][0][PFj][PCi] > 0:
					# calculating the gap
					# gap = agent.issuetree[who][len_DC+PCi][1] - agent.issuetree[who][len_DC+PCi][0]
					# print("Before: ", gap)
					gap = abs(agent.issuetree[who][len_DC+PCi][1] - (agent.issuetree[who][len_DC+PCi][0] * (1 + agent.policytree[who][0][PFj][PCi])))
					# print("After: ", gap)
				# check if the likelihood is negative
				if agent.policytree[who][0][PFj][PCi] < 0:
					# gap = agent.issuetree[who][len_DC+PCi][1] - agent.issuetree[who][len_DC+PCi][0]
					# print("Before: ", gap)
					# calculating the gap
					gap = abs(agent.issuetree[who][len_DC+PCi][1] - (agent.issuetree[who][len_DC+PCi][0] * abs(agent.policytree[who][0][PFj][PCi])))
					# print("After: ", gap)
				PF_numerator += round(gap,3)
			if PF_denominator != 0:
				agent.policytree[who][0][PFj][len_PC] = round(PF_numerator/PF_denominator,3)
			else:
				agent.policytree[who][0][PFj][len_PC] = 0

	def preference_update_PI(self, agent, who):

		"""
		The preference update function (PI)
		===========================

		This function is used to update the preferences of policy instruments the agents in their
		respective policy trees.

		agent - this is the owner of the policy tree
		who - this is the part of the policytree that is considered - agent.unique_id should be used for this - this is done to also include partial knowledge preference calculation

		"""	

		len_DC = self.len_DC
		len_PF = self.len_PC  # number of PC is always equal to number of PF
		len_PC = self.len_PC
		len_S = self.len_S

		# selecting the policy instrument from the policy family on the agenda
		PFIns_indices = self.PF_indices[self.agenda_PF]

		# calculation of the preferences for all policy instruments
		# calculation of the denominator
		PI_denominator = 0
		# going through all policy instruments
		for PIj in range(len(PFIns_indices)):
			# going through all secondary issues
			for Si in range(len_S):
				# print(" ")
				# print(PIj, Si)
				# print(agent.policytree[who][1][PFIns_indices[PIj]])
				# print(agent.policytree[who][1][PFIns_indices[PIj]][Si])
				# check if the likelihood is positive
				gap = 0
				if agent.policytree[who][1][PFIns_indices[PIj]][Si] > 0:
					# calculating the gap
					# gap = agent.issuetree[who][len_DC+len_PC+Si][1] - agent.issuetree[who][len_DC+len_PC+Si][0]
					# print("Before: ", agent.issuetree[who][len_DC+len_PC+Si][1] - agent.issuetree[who][len_DC+len_PC+Si][0], agent.policytree[who][1][PFIns_indices[PIj]][Si])
					gap = abs(agent.issuetree[who][len_DC+len_PC+Si][1] - (agent.issuetree[who][len_DC+len_PC+Si][0] * (1 + agent.policytree[who][1][PFIns_indices[PIj]][Si])))
					# print("After: ", gap)
				# check if the likelihood is negative
				if agent.policytree[who][1][PFIns_indices[PIj]][Si] < 0:
					# gap = agent.issuetree[who][len_DC+len_PC+Si][1] - agent.issuetree[who][len_DC+len_PC+Si][0]
					# print("Before: ", agent.issuetree[who][len_DC+len_PC+Si][1] - agent.issuetree[who][len_DC+len_PC+Si][0], agent.policytree[who][1][PFIns_indices[PIj]][Si])
					# calculating the gap
					gap = abs(agent.issuetree[who][len_DC + len_PC + Si][1] - (agent.issuetree[who][len_DC+len_PC+Si][0] * abs(agent.policytree[who][1][PFIns_indices[PIj]][Si])))
					# print("After: ", gap)
				PI_denominator += round(gap,3)
				# print("PI_denominator: ", PI_denominator)

		# calculation of the numerator
		# going through all policy instruments
		for PIj in range(len(PFIns_indices)):
			PI_numerator = 0
			# going through all secondary issues
			for Si in range(len_S):
				# print(" ")
				# print(PIj, Si)
				# print(agent.policytree[who][1][PFIns_indices[PIj]])
				# print(agent.policytree[who][1][PFIns_indices[PIj]][Si])
				# check if the impact is positive
				if agent.policytree[who][1][PFIns_indices[PIj]][Si] > 0:
					# calculating the gap
					# gap = agent.issuetree[who][len_DC+len_PC+Si][1] - agent.issuetree[who][len_DC+len_PC+Si][0]
					# print("Before: ", gap)
					gap = abs(agent.issuetree[who][len_DC+len_PC+Si][1] - (agent.issuetree[who][len_DC+len_PC+Si][0] * (1 + agent.policytree[who][1][PFIns_indices[PIj]][Si])))
					# print("After: ", gap)
				# check if the likelihood is negative
				if agent.policytree[who][1][PFIns_indices[PIj]][Si] < 0:
					# gap = agent.issuetree[who][len_DC+len_PC+Si][1] - agent.issuetree[who][len_DC+len_PC+Si][0]
					# print("Before: ", gap)
					# calculating the gap
					gap = abs(agent.issuetree[who][len_DC+len_PC+Si][1] - (agent.issuetree[who][len_DC+len_PC+Si][0] * abs(agent.policytree[who][1][PFIns_indices[PIj]][Si])))
					# print("After: ", gap)
				PI_numerator += round(gap,3)
			if PI_denominator != 0:
				agent.policytree[who][1][PFIns_indices[PIj]][len_S] = round(PI_numerator/PI_denominator,3)
			else:
				agent.policytree[who][1][PFIns_indices[PIj]][len_S] = 0
			# print(agent.issuetree[who][PFj])
		# print(agent.policytree[who][1])

	def conflictLevel_update_parameters(self, interest):

		"""
		The conflict level update parameter function
		===========================

		This function is used to update the conflict levels. It only outputs the value of conflict level.

		interest - the substraction of an agent's two interests
		Interests here means either issue or policy impact.

		"""	

		# low conflict value
		if interest <= 0.33:
			conflict_level = self.conflictLevel_coefficient[0]
		# medium conflict leve
		if interest > 0.33 and interest <= 0.66:
			conflict_level = self.conflictLevel_coefficient[1]
		# high conflict level
		if interest > 0.66:
			conflict_level = self.conflictLevel_coefficient[1]

		return conflict_level

	def conflictLevel_update_issue(self, agent, who):

		"""
		The conflict level issue update function
		===========================

		This function is used to update the conflict level of issues for an agent.

		agent - this is the agent whose conflict levels are updated
		who - this is the agent targetted for the conflict level

		"""	
		_unique_id = agent.unique_id
		if agent != who:  # the agent has no conflict level with itself
			# for the issues
			for issue in range(self.len_DC+self.len_PC+self.len_S):
				belief_diff = abs(agent.issuetree[_unique_id][issue][0] - who.issuetree[who.unique_id][issue][0])
				goal_diff = abs(agent.issuetree[_unique_id][issue][1] - who.issuetree[who.unique_id][issue][1])
				agent.conflictLevelIssue[who.unique_id][issue][0] = self.conflictLevel_update_parameters(belief_diff)
				agent.conflictLevelIssue[who.unique_id][issue][1] = self.conflictLevel_update_parameters(goal_diff)
			# for the causal relations
			to_cr = self.len_DC+self.len_PC+self.len_S
			for cr in range(self.len_DC*self.len_PC+self.len_PC*self.len_S):
				cr_diff = abs(agent.issuetree[_unique_id][to_cr+cr][0] - who.issuetree[who.unique_id][to_cr+cr][0])
				agent.conflictLevelIssue[who.unique_id][to_cr+cr][0] = self.conflictLevel_update_parameters(cr_diff)

	def conflictLevel_update_policy_PF(self, agent, who):

		"""
		The conflict level policy family update function
		===========================

		This function is used to update the conflict level of the policy families for an agent.

		agent - this is the agent whose conflict levels are updated
		who - this is the agent targetted for the conflict level

		"""	
		_unique_id = agent.unique_id
		if agent != who:  # the agent has no conflict level with itself
			for PFj in range(self.len_PC):
				for PCi in range(self.len_PC):
					impact_diff = abs(agent.policytree[_unique_id][0][PFj][PCi] - who.policytree[who.unique_id][0][PFj][PCi])
					agent.conflictLevelPolicy[who.unique_id][0][PFj][PCi] = self.conflictLevel_update_parameters(impact_diff)

	def conflictLevel_update_policy_PI(self, agent, who):

		"""
		The conflict level policy instruments update function
		===========================

		This function is used to update the conflict level of the policy instruments for an agent.

		agent - this is the agent whose conflict levels are updated
		who - this is the agent targetted for the conflict level

		"""	

		# selecting the policy instrument from the policy family on the agenda
		agenda_PF_change = False
		if self.agenda_PF == None:  # if there is no agenda, set one temporarily
			self.agenda_PF = 0
			agenda_PF_change = True
		PFIns_indices = self.PF_indices[self.agenda_PF]

		_unique_id = agent.unique_id
		if agent != who:  # the agent has no conflict level with itself
			for PIj in range(len(PFIns_indices)):
				for Si in range(self.len_S):
					impact_diff = abs(agent.policytree[_unique_id][1][PFIns_indices[PIj]][Si] - who.policytree[who.unique_id][1][PFIns_indices[PIj]][Si])
					agent.conflictLevelPolicy[who.unique_id][1][PFIns_indices[PIj]][Si] = self.conflictLevel_update_parameters(impact_diff)

		if agenda_PF_change == True:  # if there was no agenda, reset it to None
			self.agenda_PF = None
