from ortools.linear_solver import pywraplp
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import matplotlib as mpl
import logging

# set up logger
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
# add handler and formatting
file_handler = logging.FileHandler('patrull.log')
formatter = logging.Formatter('[%(asctime)s] %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
log.addHandler(file_handler)


def evaluate(shift, task, cost_of_shifts={1:10,2:10,3:20,4:20,5:30,6:30,7:30,8:10}, cost_of_tasks={"Patrull":20,"Post":15,"Ahi":10}):
    return cost_of_shifts[shift] + cost_of_tasks[task]


def dist_parameters(OG_shift,shifts):
    """
    Returns a list of distance parameters for a given reference shift.
    """
    l = len(shifts)
    params = {}
    for shift in shifts:
        params[shift] = (1 - abs(OG_shift-shift)/l)**2
    return params


def new_cost(data, soldier,shift,tasks,shifts, added_cost={}):
    """
    For a given soldier at a given shift returns the new costs.
    """ 
    for task in tasks:
        # check if completed task k
        if data[soldier,shift,task].solution_value() == 1:
            params = dist_parameters(shift,shifts)
            for task2 in tasks:
                for shift2 in shifts:
                    param = params[shift2]
                    if (shift2,task2) not in added_cost.keys():
                        added_cost[(shift2,task2)] = param*evaluate(shift2,task2) 
                    else:
                        added_cost[(shift2,task2)] += param*evaluate(shift2,task2)
        

        if (shift,task) not in added_cost.keys():
            added_cost[(shift,task)] = 0
    return added_cost
    

def update_costs(costs, data, names, shifts, tasks):
    for name in names:
        added_cost = {}
        for shift in shifts:
            added_cost = new_cost(data,name,shift,tasks,shifts,added_cost)
            for task in tasks:
                costs[name,shift,task] += added_cost[(shift,task)]
    return costs


def initialise_costs(names,shifts,tasks):
    """
    Initialises the cost dictionary. Assignes the 1st soldier at the first shift to the first task, 
    2nd soldier at the first shift to the 2nd task, etc.
    ---To Do---
    Might not be the best suited as it might happen that some soldiers don't have to do anything 
    during the first day.
    """
    costs = {}
    N = len(shifts)*len(tasks)/len(names)
    tasks_assigned = []
    for name in names:
        soldier_slots = 0
        shifts_assigned = []
        last_task = None
        for shift in shifts:
            for task in tasks:
                if (shift,task) not in tasks_assigned and shift not in shifts_assigned and soldier_slots < N and last_task != task:
                    costs[name,shift,task] = -evaluate(shift,task)
                    tasks_assigned.append((shift,task))
                    shifts_assigned.append(shift)
                    soldier_slots += 1
                    params = dist_parameters(shift,shifts)
                    for task2 in tasks:
                        for shift2 in shifts:
                            param = params[shift2]
                            if (shift2,task2) not in costs.keys():
                                costs[(shift2,task2)] = param*evaluate(shift2,task2) 
                            else:
                                costs[(shift2,task2)] += param*evaluate(shift2,task2)
                    last_task = task
                else:
                    costs[name,shift,task] = 0

    return costs

"""
cost = initialise_costs(names,shifts,tasks)
with open('result.txt', 'w+') as fp:
    for key in cost:
        fp.write(str(key) + ': ' + str(cost[key]) + '\n')
"""
    

def calculate_one_set(costs, names, shifts, tasks, day_number):
    # Solver
    # Create the mip solver with the SCIP backend.
    solver = pywraplp.Solver.CreateSolver("SCIP")

    if not solver:
        return

    # Variables
    data = {}
    for name in names:
        for shift in shifts:
            for task in tasks:
                data[name, shift, task] = solver.IntVar(0, 1, "")

    # Constraints
    # Each task is assigned to exactly one soldier
    for shift in shifts:
        for task in tasks:
            solver.Add(solver.Sum([data[name, shift, task] for name in names]) == 1)

    # Each soldier is assigned to at most 1 task at a given shift.
    for name in names:
        for shift in shifts:
            solver.Add(solver.Sum([data[name, shift, task] for task in tasks]) <= 1)   

    # no soldier does more than total_tasks/no_of_soldiers tasks during one night
    for name in names:
        S = 0
        for shift in shifts:
            S += solver.Sum([data[name, shift, task] for task in tasks])
        solver.Add(S <= round(len(shifts)*len(tasks)/len(names)))

    """
    for i in range(number_of_soldiers):
        res = 0
        for k in range(number_of_tasks):
            
            res += solver.Sum([x[i, j, k] for k in range(number_of_shifts)])
        solver.Add(res <= 1)
    """

    # Objective
    objective_terms = []
    for name in names:
        for shift in shifts:
            for task in tasks:
                objective_terms.append(costs[name,shift,task] * data[name,shift,task])
    solver.Minimize(solver.Sum(objective_terms))

    # Solve
    status = solver.Solve()

    # Print solution.
    if status == pywraplp.Solver.OPTIMAL or status == pywraplp.Solver.FEASIBLE:
        print(f"Total cost = {solver.Objective().Value()}\n")
        log.info("New day \n")
        log.info(f"Total cost = {solver.Objective().Value()}")
        data_copy = {}
        for name in names:
            for shift in shifts:
                for task in tasks:
                    # Test if x[i,j,k] is 1 (with tolerance for floating point arithmetic).
                    data_copy[name,shift,task] = data[name,shift,task].solution_value()
                    if data[name,shift,task].solution_value() > 0.5:
                        print(f"Soldier {name} assigned during shift {shift} to task {task}." + f" Cost: {costs[name,shift,task]}")
                        log.info(f"Soldier {name} assigned during shift {shift} to task {task}." + f" Cost: {costs[name,shift,task]}")
        # calculate new costs
        return update_costs(costs, data, names, shifts, tasks), data_copy
    else:
        print("No solution found.")
        log.warning("No solution found.")


def get_colour(task, tasks, cmap_name='Accent'):
    cm = plt.get_cmap(cmap_name)
    i = tasks.index(task)
    return cm(1.*i/len(tasks))


def get_patches(tasks):
    patches = []
    for task in tasks:
        patches.append(mpl.patches.Patch(color=get_colour(task,tasks)))
    return patches


def visualise(data,names, shifts,tasks, day):

    # Declaring a figure "gnt"
    fig, gnt = plt.subplots()

    # Setting Y-axis limits
    gnt.set_ylim(0, len(names))

    # Setting X-axis limits
    gnt.set_xlim(0, len(shifts))

    # Setting labels for x-axis and y-axis
    gnt.set_xlabel('shifts')
    gnt.set_ylabel('Names')

    
    # Labelling tickes of y-axis
    yticks = np.linspace(0.5,len(names)-0.5,len(names))
    gnt.set_yticks(yticks,labels=names,minor=True)
    

    # Setting graph attribute
    gnt.grid(True)
    cm = plt.get_cmap('Accent')

    # Declaring a bar in schedule
    i = 0
    
    for name in names:
        slots = []
        colours = []
        for shift in shifts:
            for task in tasks:
                if data[name,shift,task] > 0.5:
                    slots.append((shift-1, 1))
                    colours.append(get_colour(task,tasks))
        if slots:
            gnt.broken_barh(slots, (i, 1), facecolors = colours)
        i += 1

    # legend
    patches = get_patches(tasks)
    gnt.legend(handles=patches, labels=tasks, fontsize=11)

    plt.savefig("gantt_on_day_{}.png".format(day))


def main(no_of_days, names, shifts, tasks, costs=None):
    # initialise costs for the first day if older costs not given
    if costs == None:
        costs = initialise_costs(names,shifts,tasks)
        log.debug("Initial costs: {}".format(str(costs)))
    for day_number in range(no_of_days):
        costs, data = calculate_one_set(costs, names, shifts, tasks, day_number)
        log.debug("new costs {}\n".format(str(costs)))
        visualise(data,names,shifts,tasks, day_number)


names = ["A","B","C","D","E","F","G"]
shifts = [1,2,3,4,5,6]
tasks = ["Patrull", "Post"]

if __name__ == "__main__":
    main(5,names,shifts,tasks)

