import pandas as pd
import gurobipy as gp
import numpy as np
import os

def load(file_path):
    """
    Load data from an Excel file into a dictionary of lists.
    """
    try:
        # Read the Excel file and store data in a dictionary
        data_dict = pd.read_excel(file_path, sheet_name=None)

        # Convert each sheet's data to the appropriate format
        data = {sheet_name: data_frame.values.tolist() for sheet_name, data_frame in data_dict.items()}
        return data
    except FileNotFoundError:
        print(f"Error: File {file_path} not found.")
        exit(1)
    except PermissionError:
        print(f"No permission to access {file_path}.")
        exit(1)
    except Exception as e:
        print(f"Error loading data: {e}")
        exit(1)

def initialize(data):
    """
    Initialize the Gurobi model and define decision variables.
    """
    # Range
    num_machine = len(data["Production Rate"])
    num_part = len(data["Production Rate"][0])
    num_week = len(data["Demand"])
    valid_pair = [(i, j) for i in range(num_machine) for j in range(num_part) if data["Production Rate"][i][j] > 0]

    # Model
    m = gp.Model("Production_Scheduling")

    # Variables
    variables = {
        # Amount of a part to be producted on a machine in a week。
        "n" : m.addVars(num_machine, num_part, num_week, vtype=gp.GRB.INTEGER, lb=0, name="n"),
        # Indicating whether to produce a part on a machine in a week.
        "b" : m.addVars(num_machine, num_part, num_week, vtype=gp.GRB.BINARY, name="b"),
        # Duration of a machine operating in a week.
        "h" : m.addVars(num_machine, num_week, vtype=gp.GRB.CONTINUOUS, lb=0, name="h"),
        # Duration of overtime of a machine operating in a week.
        "v" : m.addVars(num_machine, num_week, vtype=gp.GRB.CONTINUOUS, lb=0, name="ch"),
        # Duration exceeding maximum overtime of a machine operating in a week.
        "e" : m.addVars(num_machine, num_week, vtype=gp.GRB.CONTINUOUS, lb=0, name="e"),
        # Max duration among all machines operating in a week.
        "w" : m.addVars(num_week, vtype=gp.GRB.CONTINUOUS, lb=0, name="h"),
        # Indicate whether to initially setup on a machine to product a part in a week.
        "c" : m.addVars(num_machine, num_part, num_week, vtype=gp.GRB.BINARY, name="c"),
        # Value of positive variation of "c" between consecutive weeks.
        "c_plus" : m.addVars(num_machine, num_part, num_week, vtype=gp.GRB.BINARY, name="c_plus"),
        # Value of negative variation of "c" between consecutive weeks.
        "c_minus" : m.addVars(num_machine, num_part, num_week, vtype=gp.GRB.BINARY, name="c_minus"),
        # Indicate whether to compute setup time on a machine to produce a part in a week.
        "a" : m.addVars(num_machine, num_part, num_week, vtype=gp.GRB.BINARY, name="a"),
        # Indicate the variation in setup time affected by the number of types of parts produced on a machine in a week.
        "x" : m.addVars(num_machine, num_week, vtype=gp.GRB.BINARY, name="x"),
        # Amount of a part not delivered on time in a week.
        "p" : m.addVars(num_part, num_week, vtype=gp.GRB.INTEGER, lb=0, name="p"),
        # Amount of a part to be in stock in a week.
        "t" : m.addVars(num_part, num_week, vtype=gp.GRB.INTEGER, lb=0, name="t")
    }
    return m, variables, num_machine, num_part, num_week, valid_pair

def add_constraints(m, variables, data, num_machine, num_part, num_week, valid_pair):
    """
    Define constraints for the optimization problem.
    """
    # Parameter
    P = data["Production Rate"]
    Y = data["Yield Rate"]
    S = data["Setup Time"]
    D = data["Demand"]
    M = 10000

    # Production only takes place when it is scheduled.
    for i, j in valid_pair:
        for k in range(num_week):
            m.addConstr(variables["n"][i, j, k] <= M * variables["b"][i, j, k], name=f"task_{i}{j}{k}")
    # Total production meets the total demand.
    for j in range(num_part):
        m.addConstr(gp.quicksum(variables["n"][i, j, k] for k in range(num_week) for i, _ in valid_pair if _ == j) >= gp.quicksum(D[k][j] for k in range(num_week)), name=f"total_demand_{j}")
    # Backlog from the previous week is carried over into the current week, while the stock from the previous week satisfies the demand for the current week.
    for j in range(num_part):    
        # There is no backlog or stock before the first week.
        m.addConstr(gp.quicksum(variables["n"][i, j, 0] for i, _ in valid_pair if _ == j) + variables["p"][j, 0] >= D[k][j] + variables["t"][j, 0], name=f"first_week_demand{j}{0}")
        for k in range(1, num_week - 1):
            m.addConstr(gp.quicksum(variables["n"][i, j, k] for i, _ in valid_pair if _ == j) + variables["p"][j, k] + variables["t"][j, k - 1] >= D[k][j] + variables["p"][j, k - 1] + variables["t"][j, k], name=f"every_week_demand{j}{k}")
        # There is no backlog or stock in the last week.
        m.addConstr(gp.quicksum(variables["n"][i, j, num_week - 1] for i, _ in valid_pair if _ == j) + variables["t"][j, num_week - 2] >= D[num_week - 1][j] + variables["p"][j, num_week - 2], name=f"last_week_demand_{j}{num_week - 1}")
    # Total working time is required for production and setup.
    for i, _ in valid_pair:
        for k in range(num_week):
            m.addConstr(gp.quicksum(variables["n"][i, j, k] / (P[i][j] * Y[0][j]) + S[i][j] * variables["a"][i, j, k] for _, j in valid_pair if _ == i) <= variables["h"][i, k], name=f"time_{i}{k}")
    # Time requirement
    for i in range(num_machine):
        for k in range(num_week):
            # Overtime begins when working time exceeds regular hours.
            m.addConstr(variables["v"][i, k] >= variables["h"][i, k] - 120, name=f"overtime{i}{k}")
            # Overtime exceeding maximum allowable extra hours leads to infeasible solution.
            m.addConstr(variables["v"][i, k] <= 48 + variables["e"][i, k] , name=f"exceedtime{i}{k}")
            # Weekly maximum overtime covers all machine overtime.
            m.addConstr(variables["w"][k] >= variables["v"][i, k], name=f"weektime_{k}")
    # Setup time is adjusted based on initial setup.
    for i, j in valid_pair:
        for k in range(num_week):
            m.addConstr(variables["a"][i, j, k] >= variables["b"][i, j, k] - variables["c"][i, j, k], name=f"modified_setup_{i}{j}{k}")
    # Only one is initially setup among all machines in a given week.
    for i, _ in valid_pair:
        for k in range(num_week):
            m.addConstr(gp.quicksum(variables["c"][i, j, k] for _, j in valid_pair if _ == i) == 1, name=f"onesetup_{i}{k}")
    # Initial setup depends on prior production.
    for i, j in valid_pair:
        for k in range(1, num_week):
            m.addConstr(variables["c"][i, j, k] <= variables["b"][i, j, k - 1], name=f"setup_{i}{j}{k}")
    for i, j in valid_pair:
        for k in range(num_week - 1):
            # Variation is computed in setup status between consecutive weeks.
            m.addConstr(variables["c_plus"][i, j, k] - variables["c_minus"][i, j, k] == variables["c"][i, j, k + 1] - variables["c"][i, j, k], name=f"linearization_{i}{j}{k}")
            # Variation is limited in setup status.
            m.addConstr(variables["c_plus"][i, j, k] + variables["c_minus"][i, j, k] <= 1, name=f"legalization_{i}{j}{k}")
    # Variation in setup status is matched to the number of types of parts to be produced.
    for i, _ in valid_pair:
        for k in range(num_week - 1):
            m.addConstr(gp.quicksum(variables["b"][i, j, k] for _, j in valid_pair if _ == i) <= 1 + M * variables["x"][i, k], name=f"upper_{i}{k}")
            m.addConstr(gp.quicksum(variables["b"][i, j, k] for _, j in valid_pair if _ == i) >= 2 - M * (1 - variables["x"][i, k]), name=f"lower_{i}{k}")
            m.addConstr(gp.quicksum(variables["c_plus"][i, j, k] + variables["c_minus"][i, j, k] for _, j in valid_pair if _ == i) == 2 * variables["x"][i, k], name=f"difference_{i}{j}{k}")
    return

def set_objective(m, variables, data, num_machine, num_part, num_week):
    """
    Define the objective function to minimize total costs.
    """
    # Parameters
    cost = {objective[0]: objective[1] for objective in data["Cost"]}
    priority = {objective[0]: objective[2] for objective in data["Cost"]}
    weight = {objective[0]: objective[3] for objective in data["Cost"]}
    M = 10000

    m.setObjectiveN(gp.quicksum(cost["Time"] * variables["e"][i, k] for i in range(num_machine) for k in range(num_week)), index=0, priority=priority["Time"], weight=weight["Time"])
    m.setObjectiveN(gp.quicksum(cost["Machine"] * variables["v"][i, k] for i in range(num_machine) for k in range(num_week)), index=1, priority=priority["Machine"], weight=weight["Machine"])
    m.setObjectiveN(gp.quicksum(cost["Personnel"] * variables["w"][k] for k in range(num_week)), index=2, priority=priority["Personnel"], weight=weight["Personnel"])
    m.setObjectiveN(gp.quicksum(cost["Penalty"] * variables["p"][j, k] for j in range(num_part) for k in range(num_week)), index=3, priority=priority["Penalty"], weight=weight["Penalty"])
    m.setObjectiveN(gp.quicksum(cost["Inventory"] * variables["t"][j, k] for j in range(num_part) for k in range(num_week)), index=4, priority=priority["Inventory"], weight=weight["Inventory"])
    return [objective[0] for objective in data["Cost"]]

def solve_model(m, variables, objective, num_machine, num_part, num_week, valid_pair):
    """
    Optimize the model.
    """
    # Parameter
    M = 10000

    try:
        m.optimize()
        if m.status == gp.GRB.OPTIMAL:
            # round to 4 decimal places
            np.set_printoptions(suppress=True, precision=4)
            # Initialize arrays to store results
            n_values = np.zeros((num_week, num_machine, num_part))
            b_values = np.zeros((num_week, num_machine, num_part))
            c_values = np.zeros((num_week, num_machine, num_part))
            a_values = np.zeros((num_week, num_machine, num_part))
            c_plus_values = np.zeros((num_week, num_machine, num_part))
            c_minus_values = np.zeros((num_week, num_machine, num_part))
            h_values = np.zeros((num_week, num_machine))
            v_values = np.zeros((num_week, num_machine))
            e_values = np.zeros((num_week, num_machine))
            x_values = np.zeros((num_week, num_part))
            p_values = np.zeros((num_week, num_part))
            t_values = np.zeros((num_week, num_part))
        
            # Loop over the variables and populate the values
            w_values = np.array([variables["w"][k].x for k in range(num_week)])
            for k in range(num_week):
                for i in range(num_machine):
                    h_values[k, i] = variables["h"][i, k].x
                    v_values[k, i] = variables["v"][i, k].x
                    e_values[k, i] = variables["e"][i, k].x
                for j in range(num_part):
                    x_values[k, j] = variables["x"][j, k].x
                    p_values[k, j] = variables["p"][j, k].x
                    t_values[k, j] = variables["t"][j, k].x
                for i, j in valid_pair:
                    n_values[k, i, j] = variables["n"][i, j, k].x
                    b_values[k, i, j] = variables["b"][i, j, k].x
                    c_values[k, i, j] = variables["c"][i, j, k].x
                    a_values[k, i, j] = variables["a"][i, j, k].x
                    c_plus_values[k, i, j] = variables["c_plus"][i, j, k].x
                    c_minus_values[k, i, j] = variables["c_minus"][i, j, k].x

            # Print the optimal results
            # Objective function values
            objective_values = {objective[i]: [m.getObjective(i).getValue()] for i in range(len(objective))}
            for obejctive, values in objective_values.items():
                print(f"{objective}: {values}")
            # Variable values
            variable_values = {
                "n": n_values,
                "b": b_values,
                "h": h_values,
                "v": v_values,
                "e": e_values,
                "w": w_values,
                "c": c_values,
                "c_plus": c_plus_values,
                "c_minus": c_minus_values,
                "a": a_values,
                "x": x_values,
                "p": p_values,
                "t": t_values
                }
            # Output the results
            for var_name, var_values in variable_values.items():
                print(f"Optimized {var_name} values per week:")
                for k in range(num_week):
                    print(f"Week {k + 1}:\n{var_values[k]}")
            # Generate an Excel file to store the results
            with pd.ExcelWriter("results.xlsx") as writer:
                data_frame = pd.DataFrame(objective_values)
                data_frame.to_excel(writer, sheet_name="optimal solution", index=False)
                for variable, values in variable_values.items():
                    if values.ndim == 3:
                        week_data_frame = []
                        for k in range(num_week):
                            data_frame = pd.DataFrame(values[k], columns=[f"Part {j+1}" for j in range(values.shape[2])], index=[f"Machine {i+1}" for i in range(values.shape[1])])
                            data_frame["Week"] = k + 1
                            week_data_frame.append(data_frame)
                        final_data_frame = pd.concat(week_data_frame)
                        final_data_frame.to_excel(writer, sheet_name=variable)
                    elif values.ndim == 2:
                        if variable in ["h", "v", "e"]:
                            data_frame = pd.DataFrame(values, columns=[f"Machine {i+1}" for i in range(values.shape[1])], index=[f"Week {k+1}" for k in range(values.shape[0])])
                        elif variable in ["x", "p","t"]:
                            data_frame = pd.DataFrame(values, columns=[f"Part {j+1}" for j in range(values.shape[1])], index=[f"Week {k+1}" for k in range(values.shape[0])])
                        data_frame.to_excel(writer, sheet_name=variable)
                    elif values.ndim == 1:
                        data_frame = pd.DataFrame(values, index=[f"Week {k+1}" for k in range(values.shape[0])])
                        data_frame.to_excel(writer, sheet_name=variable)
                    else:
                        raise ValueError(f"Unsupported dimension for variable {variable}")
        elif m.status == gp.GRB.INFEASIBLE:
            print("Model is infeasible.")
        else:
            print(f"Optimization ended with status {m.status}.")
    except gp.GurobiError as e:
        print(f"Gurobi Error: {e}")
    return

if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    file_path = "data.xlsx"
    data = load(file_path)
    m, variables, num_machine, num_part, num_week, valid_pair = initialize(data)
    add_constraints(m, variables, data, num_machine, num_part, num_week, valid_pair)
    objective = set_objective(m, variables, data, num_machine, num_part, num_week)
    solve_model(m, variables, objective, num_machine, num_part, num_week, valid_pair)