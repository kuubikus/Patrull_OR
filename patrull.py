from ortools.linear_solver import pywraplp
import pandas as pd
import matplotlib.pyplot as plt


def evaluate(shift, task, cost_of_shifts={1:10,2:10,3:20,4:20,5:30,6:30,7:30,8:10}, cost_of_tasks={"Patrull":20,"Post":20,"Ahi":10}):
    return cost_of_shifts[shift] + cost_of_tasks[task]


def new_cost(data, soldier,shift,tasks):
    """
    For a given soldier at a given shift returns the new costs.
    """
    added_cost = {}
    for task in tasks:
        # check if completed task k
        if data[soldier,shift,task].solution_value() == 1:
            added_cost[task] = evaluate(shift,task)
        if data[soldier,shift,task].solution_value() == 0:
            added_cost[task] = 0
    return added_cost
    

def update_costs(costs, data, names, shifts, tasks):
    for name in names:
        for shift in shifts:
            added_cost = new_cost(data,name,shift,tasks)
            for task in tasks:
                costs[name,shift,task] += added_cost[task]
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
    print("N",N)
    tasks_assigned = []
    for name in names:
        soldier_slots = 0
        shifts_assigned = []
        last_task = None
        for shift in shifts:
            for task in tasks:
                if (shift,task) not in tasks_assigned and shift not in shifts_assigned and soldier_slots < N and last_task != task:
                    costs[name,shift,task] = 10
                    tasks_assigned.append((shift,task))
                    shifts_assigned.append(shift)
                    soldier_slots += 1
                    last_task = task
                else:
                    costs[name,shift,task] = 0

    return costs


names = ["A","B","C","D","E","F","G"]
shifts = [1,2,3,4,5,6]
tasks = ["Patrull", "Post"]

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
        data_copy = {}
        for name in names:
            for shift in shifts:
                for task in tasks:
                    # Test if x[i,j,k] is 1 (with tolerance for floating point arithmetic).
                    data_copy[name,shift,task] = data[name,shift,task].solution_value()
                    if data[name,shift,task].solution_value() > 0.5:
                        print(f"Soldier {name} assigned during shift {shift} to task {task}." + f" Cost: {costs[name,shift,task]}")
        # calculate new costs
        return update_costs(costs, data, names, shifts, tasks), data_copy
    else:
        print("No solution found.")


def get_cmap(n, name='hsv'):
    '''Returns a function that maps each index in 0, 1, ..., n-1 to a distinct 
    RGB color; the keyword argument name must be a standard mpl colormap name.'''
    return plt.colormaps.get_cmap(name, n)


def visualise(data,names, shifts,tasks):

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
    gnt.set_yticklabels(names)

    # Setting graph attribute
    gnt.grid(True)
    cm = plt.get_cmap('Accent')

    # Declaring a bar in schedule
    i = 0
    NUM_COLORS = len(names)
    for name in names:
        slots = []
        for shift in shifts:
            for task in tasks:
                if not slots:
                    colour = cm(1.*i/NUM_COLORS)
                if data[name,shift,task] > 0.5:
                    slots.append((shift-1, 1))
        
        if slots:
            gnt.broken_barh(slots, (i, 1), facecolors = colour)
        i += 1

    plt.savefig("gantt1.png")



def main(no_of_days, names, shifts, tasks, costs=None):
    # initialise costs for the first day if older costs not given
    if costs == None:
        costs = initialise_costs(names,shifts,tasks)
    for day_number in range(no_of_days):
        costs, data = calculate_one_set(costs, names, shifts, tasks, day_number)
        print("new costs", costs)
    visualise(data,names,shifts,tasks)


if __name__ == "__main__":
    main(1,names,shifts,tasks)
