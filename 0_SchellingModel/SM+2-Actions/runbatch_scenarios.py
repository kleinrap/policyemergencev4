def scenario(i, exp_i, sce_i):

	if i == 15 and sce_i == 0:
		'''
		Scenario 0 - Changes
		- One PM from affiliation 0 to 1 with corresponding goal changes
		- Two PEs added to affiliation 0 with corresponding goals
		'''

		change = True
		obtained = True
		for agent in model_run_SM.schedule.agent_buffer(shuffled=False):
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

			agent = ActiveAgent((x, y), unique_id, model_run_SM, agent_type, resources, affiliation, issuetree, policytree)
			model_run_SM.preference_update(agent, unique_id)  # updating the issue tree preferences
			model_run_SM.grid.position_agent(agent, (x, y))
			model_run_SM.schedule.add(agent)

			# update of the standard inputs
			y += 1
			unique_id += 1
		
	if i == 15 and sce_i == 1:
		'''
		Scenario 1 - Changes
		- Two PEs added to affiliation 1 with corresondping goals
		'''

		obtained = True
		for agent in model_run_SM.schedule.agent_buffer(shuffled=False):
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

			agent = ActiveAgent((x, y), unique_id, model_run_SM, agent_type, resources, affiliation, issuetree, policytree)
			model_run_SM.preference_update(agent, unique_id)  # updating the issue tree preferences
			model_run_SM.grid.position_agent(agent, (x, y))
			model_run_SM.schedule.add(agent)

			# update of the standard inputs
			y += 1
			unique_id += 1

	if i == 15 and sce_i == 2:
		'''
		Scenario 2 - Changes
		- One PM from affiliation 0 to 1 with corresponding goal changes
		'''

		change = True
		for agent in model_run_SM.schedule.agent_buffer(shuffled=False):
			# changing the policy maker
			if isinstance(agent, ActiveAgent) and agent.agent_type == 'policymaker' and agent.affiliation == 0 and change == True:
				_unique_id = agent.unique_id
				
				agent.affiliation = 1
				for issue in range(7): # seven is hardcoded here - issue goals replacement
					# changing the goals to the goals of the new affiliation
					# goal_profiles_Af[Experiment][affiliation][issue + 1]
					agent.issuetree[_unique_id][issue][1] = goal_profiles_Af[exp_i][1][issue + 1]
				change = False  # stop the for loop once one agent has been changed

	if i == 1 and exp_i == 2:
		'''
		Exeperiment 2 - Changes:
		- Reverse the causal relations of agents with affiliation 1
		'''

		for agent in model_run_SM.schedule.agent_buffer(shuffled=False):
			# changing the causal relations of the agent with affiliation 1
			if isinstance(agent, ActiveAgent) and agent.affiliation == 1:
				_unique_id = agent.unique_id
				for CR in range(10): # ten is hardcoded here - issues replacement
					# goal_profiles_Af[Experiment][affiliation][issue + 1]
					agent.issuetree[_unique_id][7 + CR][0] = goal_profiles_Af[exp_i][1][7 + CR + 1]

	# # checker code
	# for agent in model_run_SM.schedule.agent_buffer(shuffled=False):
	# 	if isinstance(agent, ActiveAgent):
	# 		print(' ')
	# 		print(agent.agent_type, '\n', 'ID', agent.unique_id, 'Aff', agent.affiliation, agent.issuetree[agent.unique_id], '\n', agent.policytree[agent.unique_id])