import pandas as pd

def goal_profiles(resources_aff, exp_i, SM_version):

	input_goalProfiles_file_Ex = 'input_SM_goalProfiles_Ex0-1'
	goal_input_Ex = pd.read_csv(input_goalProfiles_file_Ex, sep=',')
	goal_profiles_Ex = []
	for i in range(len(resources_aff)*2):
		goal_profiles_Ex.append(goal_input_Ex.iloc[i].tolist())  # goal profiles for active agents and electorate

	return goal_profiles_Ex, goal_profiles_Ex
