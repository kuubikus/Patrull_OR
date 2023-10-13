from ortools.linear_solver import pywraplp

def evaluate(j):
    if j == 0:
        return 10
    if j == 1:
        return 20
    if j == 2:
        return 20
    if j == 3:
        return 10

def new_cost(i, soldiers,number_of_tasks):
    added_cost = [0 for x in range(number_of_tasks)]
    for j in range(number_of_tasks):
        # check if completed task j
        if soldiers[i,j].solution_value() == 1:
            added_cost[j] = evaluate(j)
    return added_cost
    

def update_costs(costs, soldiers):
    num_soldiers = len(costs)
    num_tasks = len(costs[0])
    res = []
    for i in range(num_soldiers):
        added_cost = new_cost(i,soldiers,num_tasks)
        res.append([costs[i][j] + added_cost[j] for j in range(num_tasks)])
    return res
    
costs = [
        [0,0,0,0],
        [0,0,0,0],
        [0,0,0,0],
        [0,0,0,0]
    ]

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
    x = {}
    for i in range(number_of_soldiers):
        for j in range(number_of_shifts):
            for k in range(number_of_tasks):
                x[i, j, k] = solver.IntVar(0, 1, "")

    # Constraints
    # Each task is assigned to exactly one worker
    for j in range(number_of_shifts):
        for k in range(number_of_tasks):
            solver.Add(solver.Sum([x[i, j, k] for i in range(number_of_soldiers)]) == 1)

    # Each worker is assigned to at most 1 task at a given shift.
    for i in range(number_of_soldiers):
        for j in range(number_of_shifts):
            solver.Add(solver.Sum([x[i, j, k] for k in range(number_of_tasks)]) <= 1)
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
                objective_terms.append(costs[i][j][k] * x[i, j, k])
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
                    if x[i, j, k].solution_value() > 0.5:
                        print(f"Worker {i} assigned during shift {j} to task {k}." + f" Cost: {costs[i][j][k]}")
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

if __name__ == "__main__":
    main(1)