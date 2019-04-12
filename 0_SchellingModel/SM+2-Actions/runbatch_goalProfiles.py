import pandas as pd

def goal_profiles(resources_aff):

	# first goal input profile
	input_goalProfiles_file_Ex1 = 'input_goalProfiles_Ex1'
	goal_input_Ex1 = pd.read_csv(input_goalProfiles_file_Ex1, sep=',')
	goal_profiles_Ex1 = []
	for i in range(len(resources_aff)*2):
		goal_profiles_Ex1.append(goal_input_Ex1.iloc[i].tolist())  # goal profiles for active agents and electorate
	# second goal input profile
	input_goalProfiles_file_Ex2 = 'input_goalProfiles_Ex2'
	goal_input_Ex2 = pd.read_csv(input_goalProfiles_file_Ex2, sep=',')
	goal_profiles_Ex2 = []
	for i in range(len(resources_aff)*2):
		goal_profiles_Ex2.append(goal_input_Ex2.iloc[i].tolist())  # goal profiles for active agents and electorate
	# third goal input profile (before change)
	input_goalProfiles_file_Ex3Be = 'input_goalProfiles_Ex3Be'
	goal_input_Ex3Be = pd.read_csv(input_goalProfiles_file_Ex3Be, sep=',')
	goal_profiles_Ex3Be = []
	for i in range(len(resources_aff)*2):
		goal_profiles_Ex3Be.append(goal_input_Ex3Be.iloc[i].tolist())  # goal profiles for active agents and electorate
	# third goal input profile (after change)
	input_goalProfiles_file_Ex3Af = 'input_goalProfiles_Ex3Af'
	goal_input_Ex3Af = pd.read_csv(input_goalProfiles_file_Ex3Af, sep=',')
	goal_profiles_Ex3Af = []
	for i in range(len(resources_aff)*2):
		goal_profiles_Ex3Af.append(goal_input_Ex3Af.iloc[i].tolist())  # goal profiles for active agents and electorate
	# fourth goal input profile (before change)
	input_goalProfiles_file_Ex4Be = 'input_goalProfiles_Ex4Be'
	goal_input_Ex4Be = pd.read_csv(input_goalProfiles_file_Ex4Be, sep=',')
	goal_profiles_Ex4Be = []
	for i in range(len(resources_aff)*2):
		goal_profiles_Ex4Be.append(goal_input_Ex4Be.iloc[i].tolist())  # goal profiles for active agents and electorate
	# fourth goal input profile (after change)
	input_goalProfiles_file_Ex4Af = 'input_goalProfiles_Ex4Af'
	goal_input_Ex4Af = pd.read_csv(input_goalProfiles_file_Ex4Af, sep=',')
	goal_profiles_Ex4Af = []
	for i in range(len(resources_aff)*2):
		goal_profiles_Ex4Af.append(goal_input_Ex4Af.iloc[i].tolist())  # goal profiles for active agents and electorate

	# putting all of the profiles into one list for the different experiments
	# splitting before and after
	goal_profiles_Be = [goal_profiles_Ex1, goal_profiles_Ex2, goal_profiles_Ex3Be, goal_profiles_Ex4Be]
	goal_profiles_Af = [goal_profiles_Ex1, goal_profiles_Ex2, goal_profiles_Ex3Af, goal_profiles_Ex4Af]

	return goal_profiles_Be, goal_profiles_Af