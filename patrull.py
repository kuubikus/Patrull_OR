from ortools.linear_solver import pywraplp

def evaluate(shift, task, cost_of_shifts=[10,10,20,20,30,30,10,10], cost_of_tasks=[20,20,10]):
    return cost_of_shifts[shift] + cost_of_tasks[task]

def new_cost(data, soldier,shift,number_of_tasks):
    """
    For a given soldier at a given shift returns the new costs.
    """
    added_cost = [0 for x in range(number_of_tasks)]
    for k in range(number_of_tasks):
        # check if completed task k
        if data[soldier,shift,k].solution_value() == 1:
            added_cost[k] = evaluate(shift,k)
    return added_cost
    

def update_costs(costs, data):

    number_of_soldiers = len(costs)
    number_of_shifts = len(costs[0])
    number_of_tasks = len(costs[0][0])

    res = []
    for i in range(number_of_soldiers):
        for j in range(number_of_shifts):
            added_cost = new_cost(data,i,j,number_of_tasks)
            res.append([costs[i][j][k] + added_cost[k] for k in range(number_of_tasks)])
    return res
    

def calculate_one_set(costs, day_number):

    number_of_soldiers = len(costs)
    number_of_shifts = len(costs[0])
    number_of_tasks = len(costs[0][0])

    # Solver
    # Create the mip solver with the SCIP backend.
    solver = pywraplp.Solver.CreateSolver("SCIP")

    if not solver:
        return

    # Variables
    # x[i, j, k] is an array of 0-1 variables, which will be 1
    # if soldier i is assigned to shift j and task k.
    data = {}
    for i in range(number_of_soldiers):
        for j in range(number_of_shifts):
            for k in range(number_of_tasks):
                data[i, j, k] = solver.IntVar(0, 1, "")

    # Constraints
    # Each task is assigned to exactly one worker
    for j in range(number_of_shifts):
        for k in range(number_of_tasks):
            solver.Add(solver.Sum([data[i, j, k] for i in range(number_of_soldiers)]) == 1)

    # Each worker is assigned to at most 1 task at a given shift.
    for i in range(number_of_soldiers):
        for j in range(number_of_shifts):
            solver.Add(solver.Sum([data[i, j, k] for k in range(number_of_tasks)]) <= 1)
    """
    for i in range(number_of_soldiers):
        res = 0
        for k in range(number_of_tasks):
            
            res += solver.Sum([x[i, j, k] for k in range(number_of_shifts)])
        solver.Add(res <= 1)"""

    # Objective
    objective_terms = []
    for i in range(number_of_soldiers):
        for j in range(number_of_shifts):
            for k in range(number_of_tasks):
                objective_terms.append(costs[i][j][k] * data[i, j, k])
    solver.Minimize(solver.Sum(objective_terms))

    # Solve
    status = solver.Solve()

    # Print solution.
    if status == pywraplp.Solver.OPTIMAL or status == pywraplp.Solver.FEASIBLE:
        print(f"Total cost = {solver.Objective().Value()}\n")
        for i in range(number_of_soldiers):
            for j in range(number_of_shifts):
                for k in range(number_of_tasks):
                    # Test if x[i,j,k] is 1 (with tolerance for floating point arithmetic).
                    if data[i, j, k].solution_value() > 0.5:
                        print(f"Worker {i} assigned during shift {j} to task {k}." + f" Cost: {costs[i][j][k]}")
        # calculate new costs
        return update_costs(costs, data)
    else:
        print("No solution found.")


def main(no_of_days):
    # initialise 
    costs = [
        [[0,10],[10,10],[10,10],[10,0]],
        [[10,10],[0,10],[10,0],[10,10]],
        [[10,10],[10,0],[0,10],[10,10]],
        [[10,0],[10,10],[10,10],[0,10]]
    ]
    for day_number in range(no_of_days):
        costs = calculate_one_set(costs,day_number)
        print("new costs", costs)

if __name__ == "__main__":
    main(1)