from model_SM_schelling import Schelling
from model_SM_PE import PolicyEmergenceSM
import matplotlib.pyplot as plt
import copy
import pandas as pd
import time

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
repetitions_runs = 50
exp_number = 1
sce_number = 1


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
sch_homophilyType1 = 0.3  # homophily of type 1 agents
sch_movementQuota = 0.30  # initial movement quota
sch_happyCheckRadius = 5  # initial happiness check radius
sch_moveCheckRadius = 10  # initial movement check radius
sch_last_move_quota = 5  # initial last moment quota

''' parameters of the policy emergence model '''
# SM+0 parameters
PE_PMs = 4  # number of policy makers
PE_PMs_aff = [2, 2]  # policy maker distribution per affiliation
PE_PEs = 8  # number of policy entrepreneurs
PE_PEs_aff = [4, 4]  # policy entrepreneur distribution per affiliation
PE_EPs = 2  # number of external parties
PE_EPs_aff = [1, 1]  # external parties distribution per affiliation
resources_aff = [0.25, 1.00]  # resources per affiliation agent out of 1
representativeness = [25, 75]  # electorate representativeness per affiliation
# goal_profiles_Be, goal_profiles_Af = goal_profiles(resources_aff, SM_version)  # getting the goal profiles

# SM+2 parameters
# conflict level coefficient [low, medium, high]
conflictLevel_coefficient = [0.75, 0.95, 0.85]
weightAction = 1  # used to calibrate the policy learning speed ... numbers above one mean higher policy learning speed
weightResources = 1/5  # helps define the number of actions the agents can make per step
weightBonusPM = 1.05  # bonus when policy makers are targeted in the PF step
action_param = [weightAction, weightResources, weightBonusPM]
init_randomness = 25 # initial randomness of the goals of the agents
# scenario_input = [None, None, None, None, None] # setting for the Schelling scenarios by default

# scenarios for the different runs (policy emergence model) - mid point changes
def scenario_PE_mid():

	'''
	Below are all the changes related to the SCENARIOS AND EXPERIMENTS for the policy emergence model
	These changes are happening at the midway point of the simulation.
	Three scenarios are being considered. The details are provided in the formalisation report.
	One of the experiment is also included as it contains a change in the causal relations of the agents of affiliation 1 mid-simulation.
	'''

	simulation_midpoint = 15

	# redefining the issue tree basics - hardcoded values for simplicity
	issuetree_virgin = issuetree_creation(model_run_PE, model_run_PE.len_DC, model_run_PE.len_PC, model_run_PE.len_S, model_run_PE.len_CR)
	policytree_virgin = policytree_creation(model_run_PE, model_run_PE.len_PC, model_run_PE.len_S, model_run_PE.len_PC, model_run_PE.len_ins_1, model_run_PE.len_ins_2, model_run_PE.len_ins_all)

	if SM_version == 2:

		if i == simulation_midpoint and sce_i == 0:
			'''
			Changing the resources of the agents (flip)
			'''

			resources_aff = [1, 0.25]

			for agent in model.schedule.agent_buffer(shuffled=False):
				if agent.affiliation == 0:
					agent.resources = resources_aff[0]
				if agent.affiliation == 1:
					agent.resources = resources_aff[1]


# scenarios for the different runs (policy emergence model) - initial settings
def scenario_PE_start():

	'''
	Below are all the experiment related inputs for the policy emergence model
	'''

	resources_aff = [0.25, 1.00]  # resources per affiliation agent out of 1
	goal_profiles_Be, goal_profiles_Af = goal_profiles(resources_aff, exp_i, SM_version)  # getting the goal profiles

	# per version changes
	if SM_version == 2:

		if sce_i == 0:
			'''
			Scenario 0 - Resource distribution
			- Equal resources
			'''

			resources_aff = [0.25, 1.00]  # resources per affiliation agent out of 1

	return resources_aff, goal_profiles_Be, goal_profiles_Af

# scenarios for the different runs (schelling model)
def scenario_Sch():

	'''
	Below are all the changes related to the SCENARIOS AND EXPERIMENTS for the Schelling segregation model
	These changes are happening at the midway point of the simulation.
	'''

	simulation_midpoint = 15

	if i != simulation_midpoint:
		scenario_input = [None, None, None, None, None]
		return scenario_input

	if i == simulation_midpoint:
		happyCheckRadius = None
		movementQuota = 0.70
		last_move_quota = 1
		homophilyType0 = 0.65
		homophilyType1 = 0.50
		scenario_input = [happyCheckRadius, movementQuota, last_move_quota, homophilyType0, homophilyType1]
		return scenario_input


	# # checker code
	# for agent in model_run_PE.schedule.agent_buffer(shuffled=False):
	# 	if isinstance(agent, ActiveAgent):
	# 		print(' ')
	# 		print(agent.agent_type, '\n', 'ID', agent.unique_id, 'Aff', agent.affiliation, agent.issuetree[agent.unique_id], '\n', agent.policytree[agent.unique_id])

# running a number of experiments
for exp_i in range(exp_number):

	# running a number of scenarios
	for sce_i in range (sce_number):

		# initialising scenarios
		resources_aff, goal_profiles_Be, goal_profiles_Af = scenario_PE_start()

		# creating the agents for the policy emergence model
		PE_inputs = [PE_PMs, PE_PMs_aff, PE_PEs, PE_PEs_aff, PE_EPs, PE_EPs_aff, resources_aff, representativeness, goal_profiles_Be, conflictLevel_coefficient, init_randomness]

		# running a number of repetitions per experiment
		for rep_runs in range(repetitions_runs):

			start = time.time()

			# for tests and part runs
			if sce_i >= 0:

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
						scenario_input = [None, None, None, None, None]
						for warmup_time in range(warmup_tick):

							IssueInit, type0agents, type1agents = model_run_schelling.step(policy_chosen, scenario_input)

					# policy impact evaluation
					policy_impact_evaluation(model_run_PE, model_run_schelling, IssueInit, interval_tick)

					# running the policy emergence model
					if i == 0:
						KPIs = issue_mapping(IssueInit, type0agents, type1agents)
					else:
						KPIs = issue_mapping(KPIs, type0agents, type1agents)
					policy_chosen = model_run_PE.step(SM_version, KPIs, action_param)


					# run of the segregation model for n ticks
					scenario_input = scenario_Sch()
					for p in range(interval_tick):
						KPIs, type0agents, type1agents = model_run_schelling.step(policy_chosen, scenario_input)
						scenario_input = [None, None, None, None, None] # reset the scenario input
						policy_chosen = [None for ite in range(len(model_run_PE.policy_instruments[0]))] # reset policy after it has been implemented once

					# running the different scenarios
					scenario_PE_mid()

				# output of the data
				# Schelling model
				output_Schelling_model = model_run_schelling.datacollector.get_model_vars_dataframe()
				output_Schelling_model.to_csv('O_SM' + str(SM_version) + '_Sch_model_Exp' + str(exp_i) + '_Sce' + str(sce_i) + '_Run' + str(rep_runs) + '.csv')
				# dataPlot_Schelling_agents = model_run_schelling.datacollector.get_agent_vars_dataframe()
				# dataPlot_Schelling_agents.to_csv('O_Sch_agents_' + str(exp_i) + '_Sce' + str(sce_i) + '_Run' + str(rep_runs) + '.csv')  # agents are not needed a this point

				# policy emergence model
				output_PE_model = model_run_PE.datacollector.get_model_vars_dataframe()
				output_PE_model.to_csv('O_SM' + str(SM_version) + '_PE_model_Exp' + str(exp_i) + '_Sce' + str(sce_i) + '_Run' + str(rep_runs) + '.csv')
				output_PE_agents = model_run_PE.datacollector.get_agent_vars_dataframe()
				output_PE_agents.to_csv('O_SM' + str(SM_version) + '_PE_agents_Exp' + str(exp_i) + '_Sce' + str(sce_i) + '_Run' + str(rep_runs) + '.csv')

			end = time.time()

			print('Simulation time:', end-start)
