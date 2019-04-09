import pandas as pd
import matplotlib.pyplot as plt
import ast

'''
This is a file that is used to extract the data from the SM - policy emergence Schelling model results.
There are three experiments, three scenarios and 5 repetitions for each (more are coming for testing purposes)
'''
# global parameters
total_runs = 30

# FOCUSING ON THE RESULTS OF THE SCHELLING MODEL
# initialisation of lists
Sch_model = []

# the different columns of the panda
# ['Unnamed: 0', 'step', 'happy', 'happytype0', 'happytype1', 'movement', 'movementtype0', 'movementtype1', 'evenness', 'numberOfAgents', 'homophilyType0', 'homophilyType1', 'movementQuota', 'happyCheckRadius', 'last_move_quota']
steps_Sch = []
happy = []
happytype0 = []
happytype1 = []
movement = []
movementtype0 = []
movementtype1 = []
evenness = []
numberOfAgents = []
homophilyType0 = []
homophilyType1 = []
movementQuota = []
happyCheckRadius = []
last_move_quota = []

# We first read all the files into arrays that contains each entire file
for i in range(total_runs):
	print('Run read: ' + str(i))
	Sch_model.append(pd.read_csv('O_SchAlone_model_' + str(i) + '.csv'))

	steps_Sch.append([])
	happy.append([])
	happytype0.append([])
	happytype1.append([])
	movement.append([])
	movementtype0.append([])
	movementtype1.append([])
	evenness.append([])
	numberOfAgents.append([])
	homophilyType0.append([])
	homophilyType1.append([])
	movementQuota.append([])
	happyCheckRadius.append([])
	last_move_quota.append([])

# reading the head of the panda
print(list(Sch_model[0].head(0)))

# saving the paremeters in different arrays
for i in range(total_runs):
	for index, row in Sch_model[i].iterrows():
		steps_Sch[i].append(index)
		happy[i].append(row['happy'])
		happytype0[i].append(row['happytype0'])
		happytype1[i].append(row['happytype1'])
		movement[i].append(row['movement'])
		movementtype0[i].append(row['movementtype0'])
		movementtype1[i].append(row['movementtype1'])
		evenness[i].append(row['evenness'])
		numberOfAgents[i].append(row['numberOfAgents'])
		homophilyType0[i].append(row['homophilyType0'])
		homophilyType1[i].append(row['homophilyType1'])
		movementQuota[i].append(row['movementQuota'])
		happyCheckRadius[i].append(row['happyCheckRadius'])
		last_move_quota[i].append(row['last_move_quota'])


for i in range(total_runs):
# 	numberOfAgentsmovementQuota = [i] = movementQuota[i]*numberOfAgents[i]
	movementQuota[i] = [x*numberOfAgents[i][0] for x in movementQuota[i]]


# DOING ALL OF THE PLOTTING
# Looking at all the models at once for all technical model variables
f, axarr = plt.subplots(1, 3, figsize=(11,3.5))
for i in range(total_runs):
	axarr[0].plot(steps_Sch[i], happy[i], color = 'r', linewidth=1, label='Happy')
	axarr[0].plot(steps_Sch[i], happytype0[i], color = 'g', linewidth=1, label='Happy 0')
	axarr[0].plot(steps_Sch[i], happytype1[i], color = 'b', linewidth=1, label='Happy 1')
# plt.legend(handles=[burnt_line, camp_site_line, empy_line, thick_forest_line, thin_forest_line])
axarr[0].set_title('Happiness')
axarr[0].set_xlim([0, 160])
axarr[0].set_ylim([0, 350])
axarr[0].legend
axarr[0].grid(True)

for i in range(total_runs):
	axarr[1].plot(steps_Sch[i], movement[i], color = 'r', linewidth=1, label='Movement')
	axarr[1].plot(steps_Sch[i], movementtype0[i], color = 'g', linewidth=1, label='Movement 0')
	axarr[1].plot(steps_Sch[i], movementtype1[i], color = 'b', linewidth=1, label='Movement 1')
	axarr[1].plot(steps_Sch[i], movementQuota[i], color = 'k', linewidth=1, label='movementQuota')
# plt.legend(handles=[movement, movementtype1 , movementtype2])
axarr[1].set_title('Movement')
axarr[1].set_xlim([0, 160])
axarr[1].set_ylim([0, 250])
axarr[1].legend
axarr[1].grid(True)

print("test", numberOfAgents[i][0])

# for i in range(total_runs):
# 	axarr[2].plot(steps_Sch[i], homophilyType0[i], color = 'g', linewidth=1, label='homophilyType0')
# 	axarr[2].plot(steps_Sch[i], homophilyType1[i], color = 'b', linewidth=1, label='homophilyType1')
	
# # plt.legend(handles=[movement, movementtype1 , movementtype2])
# axarr[2].set_title('Homophily')
# axarr[2].set_xlim([0, 160])
# axarr[2].set_ylim([0, 1])
# axarr[2].legend
# axarr[2].grid(True)

for i in range(total_runs):
	axarr[2].plot(steps_Sch[i], evenness[i], color = 'r', linewidth=1, label='evenness')
	# axarr[3].plot(steps[i], homophilyType0[i], color = 'g', linewidth=1, label='homophilyType1')
# plt.legend(handles=[movement, movementtype1 , movementtype2])
axarr[2].set_title('evenness')
axarr[2].set_xlim([0, 160])
axarr[2].set_ylim([0, 1])
axarr[2].legend
axarr[2].grid(True)

plt.show()




