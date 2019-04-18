from model_SM_schelling import Schelling
from model_SM_PE import PolicyEmergenceSM
import matplotlib.pyplot as plt
import copy
import pandas as pd
import os

from model_SM_PE_policyImpact import policy_impact_evaluation
from model_module_interface import issue_mapping
from model_SM_PE_agents import TruthAgent, ActiveAgent
from model_SM_PE_agents_initialisation import issuetree_creation, policytree_creation
from runbatch_goalProfiles import goal_profiles

'''
The architecture present here is to be used for performing experiments. A batch runner algorithm will be used such that a set of experiments can be run at the same time.
'''

''' model version '''
# 0 - SM, 1 - SM+1 electorate, 2 - SM+2 actions, 3 - SM+3 networks, 4 - SM+4 bounded, 5 - SM+5 coalitions
SM_version = 2

# batch run parameters
repetitions_runs = 5
exp_number = 0

''' general running parameters '''
total_ticks = 155
interval_tick = 5
run_tick = int(total_ticks/interval_tick)
warmup_tick = interval_tick

''' parameters of the Schelling model'''
sch_height = 20  # height of the grid - this value must be a multiple of 4
sch_width = 20  # width of the grid - this value must be a multiple of 4
sch_density = 0.8  # agent percentage density on the grid
sch_minority_pc = 0.4  # percentage of type 1 agents compared to type 0
sch_homophilyType0 = 0.7  # homophily of type 0 agents
sch_homophilyType1 = 0.5  # homophily of type 1 agents
sch_movementQuota = 0.30  # initial movement quota
sch_happyCheckRadius = 5  # initial happiness check radius
sch_moveCheckRadius = 10  # initial movement check radius
sch_last_move_quota = 5  # initial last moment quota

''' parameters of the policy emergence model '''
# SM+0 parameters
PE_PMs = 3  # number of policy makers
PE_PMs_aff = [2, 1]  # policy maker distribution per affiliation
PE_PEs = 4  # number of policy entrepreneurs
PE_PEs_aff = [2, 2]  # policy entrepreneur distribution per affiliation
PE_EPs = 2  # number of external parties
PE_EPs_aff = [1, 1]  # external parties distribution per affiliation
resources_aff = [0.75, 0.75]  # resources per affiliation agent out of 100
representativeness = [25, 75]  # electorate representativeness per affiliation
goal_profiles_Be, goal_profiles_Af = goal_profiles(resources_aff)  # getting the goal profiles

# SM+2 parameters
# conflict level coefficient [low, medium, high]
conflictLevel_coefficient = [0.75, 0.95, 0.85]
actionWeight = 1  # used to calibrate the policy learning speed ... numbers above one mean higher policy learning speed
resourcesWeight = 1/5  # helps define the number of actions the agents can make per step
action_param = [actionWeight, resourcesWeight]

# scenarios for the different runs
def scenario():

	'''
	Below are all the changes related to the SCENARIOS AND EXPERIMENTS
	These changes are happening at the midway point of the simulation.
	Three scenarios are being considered. The details are provided in the formalisation report.
	One of the experiment is also included as it contains a change in the causal relations of the agents of affiliation 1 mid-simulation.
	'''

	simulation_midpoint = 15

	# redefining the issue tree basics - hardcoded values for simplicity
	issuetree_virgin = issuetree_creation(model_run_PE, model_run_PE.len_DC, model_run_PE.len_PC, model_run_PE.len_S, model_run_PE.len_CR)
	policytree_virgin = policytree_creation(model_run_PE, model_run_PE.len_PC, model_run_PE.len_S, model_run_PE.len_PC, model_run_PE.len_ins_1, model_run_PE.len_ins_2, model_run_PE.len_ins_all)

	if i == simulation_midpoint and sce_i == 0:
		'''
		Scenario 0 - Changes
		- One PM from affiliation 0 to 1 with corresponding goal changes
		- Two PEs added to affiliation 0 with corresponding goals
		'''

		change = True
		obtained = True
		for agent in model_run_PE.schedule.agent_buffer(shuffled=False):
			# changing the policy maker
			if isinstance(agent, ActiveAgent) and agent.agent_type == 'policymaker' and agent.affiliation == 0 and change == True:
				_unique_id = agent.unique_id
				
				agent.affiliation = 1
				for issue in range(7): # seven is hardcoded here - issue goals replacement
					# changing the goals to the goals of the new affiliation
					# goal_profiles[Experiment][affiliation][issue + 1]
					agent.issuetree[_unique_id][issue][1] = goal_profiles_Af[exp_i][1][issue + 1]
				change = False  # stop the for loop once one agent has been changed

			# adapting the size of the issuetree and the policytree
			if isinstance(agent, ActiveAgent):
				for added_tree in range(2):  # number of added agents
					agent.issuetree.append(issuetree_virgin)
					agent.policytree.append(policytree_virgin)

			# obtaining the issue tree for thepolicy entrepreneur
			if isinstance(agent, ActiveAgent) and agent.affiliation == 0 and obtained == True:
				_unique_id = copy.deepcopy(agent.unique_id)
				_issuetree_0 = copy.deepcopy(agent.issuetree)
				_issuetree_0[_unique_id] = _issuetree_0[_unique_id + 1]  # making sure to reset the issue tree
				_policytree_0 = copy.deepcopy(agent.policytree)
				_policytree_0[_unique_id] = _policytree_0[_unique_id + 1]  # making sure to reset the policy tree
				obtained = False

		# adding two PEs to affiliation 0
		x = 55
		y = 55
		unique_id = 10
		for add_PEs in range(2):					
			agent_type = 'policyentrepreneur'
			affiliation = 0
			resources = 0  # not important for this model
			issuetree = copy.deepcopy(_issuetree_0)
			# introducing the issues
			for issue in range(7): # seven is hardcoded here - caural relations replacement
				# changing the goals to the goals of the new affiliation
				# goal_profiles[Experiment][affiliation][issue + 1]
				issuetree[unique_id][issue][1] = goal_profiles_Af[exp_i][affiliation][issue + 1]
			for CR in range(10): # ten is hardcoded here - issues replacement
				# goal_profiles[Experiment][affiliation][issue + 1]
				issuetree[unique_id][7 + CR][0] = goal_profiles_Af[exp_i][affiliation][7 + CR + 1]

			policytree = copy.deepcopy(_policytree_0)

			agent = ActiveAgent((x, y), unique_id, model_run_PE, agent_type, resources, affiliation, issuetree, policytree)
			model_run_PE.preference_update(agent, unique_id)  # updating the issue tree preferences
			model_run_PE.grid.position_agent(agent, (x, y))
			model_run_PE.schedule.add(agent)

			# update of the standard inputs
			y += 1
			unique_id += 1
		
	if i == simulation_midpoint and sce_i == 1:
		'''
		Scenario 1 - Changes
		- Two PEs added to affiliation 1 with corresondping goals
		'''

		obtained = True
		for agent in model_run_PE.schedule.agent_buffer(shuffled=False):
			# adapting the size of the issuetree and the policytree
			if isinstance(agent, ActiveAgent):
				for added_tree in range(2):  # number of added agents
					agent.issuetree.append(issuetree_virgin)
					agent.policytree.append(policytree_virgin)

			# obtaining the issue tree for thepolicy entrepreneur
			if isinstance(agent, ActiveAgent) and agent.affiliation == 1 and obtained == True:
				_unique_id = copy.deepcopy(agent.unique_id)
				_issuetree_0 = copy.deepcopy(agent.issuetree)
				_issuetree_0[_unique_id] = _issuetree_0[_unique_id + 1]  # making sure to reset the issue tree
				_policytree_0 = copy.deepcopy(agent.policytree)
				_policytree_0[_unique_id] = _policytree_0[_unique_id + 1]  # making sure to reset the policy tree
				obtained = False

		# adding two PEs to affiliation 0
		x = 55
		y = 55
		unique_id = 10
		for add_PEs in range(2):					
			agent_type = 'policyentrepreneur'
			affiliation = 1
			resources = 0  # not important for this model
			issuetree = copy.deepcopy(_issuetree_0)
			# introducing the issues
			for issue in range(7): # seven is hardcoded here - caural relations replacement
				# changing the goals to the goals of the new affiliation
				# goal_profiles_Af[Experiment][affiliation][issue + 1]
				issuetree[unique_id][issue][1] = goal_profiles_Af[exp_i][affiliation][issue + 1]
			for CR in range(10): # ten is hardcoded here - issues replacement
				# goal_profiles_Af[Experiment][affiliation][issue + 1]
				issuetree[unique_id][7 + CR][0] = goal_profiles_Af[exp_i][affiliation][7 + CR + 1]

			policytree = copy.deepcopy(_policytree_0)

			agent = ActiveAgent((x, y), unique_id, model_run_PE, agent_type, resources, affiliation, issuetree, policytree)
			model_run_PE.preference_update(agent, unique_id)  # updating the issue tree preferences
			model_run_PE.grid.position_agent(agent, (x, y))
			model_run_PE.schedule.add(agent)

			# update of the standard inputs
			y += 1
			unique_id += 1

	if i == simulation_midpoint and sce_i == 2:
		'''
		Scenario 2 - Changes
		- One PM from affiliation 0 to 1 with corresponding goal changes
		'''

		change = True
		for agent in model_run_PE.schedule.agent_buffer(shuffled=False):
			# changing the policy maker
			if isinstance(agent, ActiveAgent) and agent.agent_type == 'policymaker' and agent.affiliation == 0 and change == True:
				_unique_id = agent.unique_id
				
				agent.affiliation = 1
				for issue in range(7): # seven is hardcoded here - issue goals replacement
					# changing the goals to the goals of the new affiliation
					# goal_profiles_Af[Experiment][affiliation][issue + 1]
					agent.issuetree[_unique_id][issue][1] = goal_profiles_Af[exp_i][1][issue + 1]
				change = False  # stop the for loop once one agent has been changed

	if i == simulation_midpoint and exp_i == 2:
		'''
		Exeperiment 2 - Changes:
		- Reverse the causal relations of agents with affiliation 1
		'''

		for agent in model_run_PE.schedule.agent_buffer(shuffled=False):
			# changing the causal relations of the agent with affiliation 1
			if isinstance(agent, ActiveAgent) and agent.affiliation == 1:
				_unique_id = agent.unique_id
				for CR in range(10): # ten is hardcoded here - issues replacement
					# goal_profiles_Af[Experiment][affiliation][issue + 1]
					agent.issuetree[_unique_id][7 + CR][0] = goal_profiles_Af[exp_i][1][7 + CR + 1]

	# # checker code
	# for agent in model_run_PE.schedule.agent_buffer(shuffled=False):
	# 	if isinstance(agent, ActiveAgent):
	# 		print(' ')
	# 		print(agent.agent_type, '\n', 'ID', agent.unique_id, 'Aff', agent.affiliation, agent.issuetree[agent.unique_id], '\n', agent.policytree[agent.unique_id])

# running a number of experiments
for exp_i in range(4):

	# running a number of scenarios
	for sce_i in range (3):

		# creating the agents for the policy emergence model
		PE_inputs = [PE_PMs, PE_PMs_aff, PE_PEs, PE_PEs_aff, PE_EPs, PE_EPs_aff, resources_aff, representativeness, goal_profiles_Be[exp_i], conflictLevel_coefficient]

		# running a number of repetitions per experiment
		for rep_runs in range(repetitions_runs):

			# for tests and part runs
			if exp_i == 3:

				# initialisation of the Schelling model
				model_run_schelling = Schelling(sch_height, sch_width, sch_density, sch_minority_pc, sch_homophilyType0, sch_homophilyType1, sch_movementQuota, sch_happyCheckRadius, sch_moveCheckRadius, sch_last_move_quota)

				# initialisation of the policy emergence model
				model_run_PE = PolicyEmergenceSM(PE_inputs, 10,10)

				print("\n")
				print("************************")
				print("Start of the simulation:", "\n")
				for i in range(run_tick):

					print(" ")
					print("************************")
					print("Tick number: ", i, ', experiment:', exp_i, ', scenario:', sce_i)

					# warm up time
					# this is also used as a warmup time
					if i == 0:
						policy_chosen = [None for ite in range(len(model_run_PE.policy_instruments[0]))]
						for warmup_time in range(warmup_tick):
							IssueInit, type0agents, type1agents = model_run_schelling.step(policy_chosen)

					# policy impact evaluation
					policy_impact_evaluation(model_run_PE, model_run_schelling, IssueInit, interval_tick)

					# running the policy emergence model
					if i == 0:
						KPIs = issue_mapping(IssueInit, type0agents, type1agents)
					else:
						KPIs = issue_mapping(KPIs, type0agents, type1agents)
					policy_chosen = model_run_PE.step(SM_version, KPIs, action_param)

					# run of the segregation model for n ticks
					for p in range(interval_tick):
						KPIs, type0agents, type1agents = model_run_schelling.step(policy_chosen)
						policy_chosen = [None for ite in range(len(model_run_PE.policy_instruments[0]))] # reset policy after it has been implemented once

					# running the different scenarios
					scenario()

				# output of the data
				# Schelling model
				output_Schelling_model = model_run_schelling.datacollector.get_model_vars_dataframe()
				output_Schelling_model.to_csv('O_Sch_model_' + str(exp_i) + '_Sce' + str(sce_i) + '_Run' + str(rep_runs) + '.csv')
				# dataPlot_Schelling_agents = model_run_schelling.datacollector.get_agent_vars_dataframe()
				# dataPlot_Schelling_agents.to_csv('O_Sch_agents_' + str(exp_i) + '_Sce' + str(sce_i) + '_Run' + str(rep_runs) + '.csv')  # agents are not needed a this point

				# policy emergence model
				output_PE_model = model_run_PE.datacollector.get_model_vars_dataframe()
				output_PE_model.to_csv('O_SM_model_Exp' + str(exp_i) + '_Sce' + str(sce_i) + '_Run' + str(rep_runs) + '.csv')
				output_PE_agents = model_run_PE.datacollector.get_agent_vars_dataframe()
				output_PE_agents.to_csv('O_SM_agents_' + str(exp_i) + '_Sce' + str(sce_i) + '_Run' + str(rep_runs) + '.csv')

