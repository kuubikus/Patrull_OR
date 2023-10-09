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
    
    num_soldiers = len(costs)
    num_of_diff_tasks = len(costs[0])
    num_of_shifts = len(costs[0][0])

    # Solver
    # Create the mip solver with the SCIP backend.
    solver = pywraplp.Solver.CreateSolver("SCIP")

    if not solver:
        return None

    # Variables
    # x is a dictionary where a key points to a specifc soldier.
    # Each soldier has m lists with length n, where 1 means he has that shift.
    # m is the number of different tasks (post, patrole etc).
    # n is the number of shifts during the period.
    x = {}
    for i in range(num_soldiers):
        x[i] = [[] for n in range(num_of_diff_tasks)]
        for l in range(num_of_shifts):
            x[i].append(solver.IntVar(0, 1, ""))

    
    # Constraints
    # Each soldier is assigned to at most 3 shifts.
    for i in range(num_soldiers):
        shifts_done = 0
        for j in range(num_of_diff_tasks):
            shifts_done += solver.Sum([x[i][j][n] for n in range(num_of_shifts)])
        solver.Add(shifts_done <= 3)

    # Each soldier is assigned to at most 1 task at a time. E.g a soldier can't patrole twice
    for i in range(num_soldiers):
        tasks_done = 0
        for j in range(num_of_diff_tasks):
            solver.add(solver.)


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
                    print(f"Worker {i} assigned to task {j} on day {day_number}." + f" Cost: {costs[i][j]}")
        new_costs = update_costs(costs,x)
        return new_costs
    else:
        print("No solution found.")
        return False


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