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

    num_workers = len(costs)
    num_tasks = len(costs[0])

    # Solver
    # Create the mip solver with the SCIP backend.
    solver = pywraplp.Solver.CreateSolver("SCIP")

    if not solver:
        return

    # Variables
    # x[i, j] is an array of 0-1 variables, which will be 1
    # if worker i is assigned to task j.
    x = {}
    for i in range(num_workers):
        for j in range(num_tasks):
            x[i, j] = solver.IntVar(0, 1, "")

    # Constraints
    # Each worker is assigned to at most 1 task.
    for i in range(num_workers):
        solver.Add(solver.Sum([x[i, j] for j in range(num_tasks)]) <= 1)

    # Each task is assigned to exactly one worker.
    for j in range(num_tasks):
        solver.Add(solver.Sum([x[i, j] for i in range(num_workers)]) == 1)

    # Objective
    objective_terms = []
    for i in range(num_workers):
        for j in range(num_tasks):
            objective_terms.append(costs[i][j] * x[i, j])
    solver.Minimize(solver.Sum(objective_terms))

    # Solve
    status = solver.Solve()

    # Print solution.
    if status == pywraplp.Solver.OPTIMAL or status == pywraplp.Solver.FEASIBLE:
        print(f"Total cost = {solver.Objective().Value()}\n")
        for i in range(num_workers):
            for j in range(num_tasks):
                # Test if x[i,j] is 1 (with tolerance for floating point arithmetic).
                if x[i, j].solution_value() > 0.5:
                    print(f"Worker {i} assigned to task {j}." + f" Cost: {costs[i][j]}")
    else:
        print("No solution found.")


if __name__ == "__main__":
    main()


def main(no_of_days):
    # initialise 
    costs = [
        [0,10,10,10],
        [10,0,10,10],
        [10,10,0,10],
        [10,10,10,0]
    ]
    for day_number in range(no_of_days):
        costs = calculate_one_set(costs,day_number)

if __name__ == "__main__":
    main(2)