# production-scheduling-case
This project contains a Mixed-Integer Programming (MIP) model designed to solve production scheduling problems using the Gurobi optimizer.

This model is based on the case presented in the following article:
B. Madhu Rao, Jeroen Beliën (2014) Case—Production Scheduling at Falcon Die Casting. INFORMS Transactions on Education 15(1):154-155. [https://doi.org/10.1287/ited.2014.0132cs](https://doi.org/10.1287/ited.2014.0132cs)

---

## Overview

The MIP model addresses the following key components of production scheduling:
1. **Objective**: Minimize total production costs, including labor, machien maintenance and inventory.
2. **Constraints**:
  - To be completed

---

## Requirements

To run the MIP model, ensure you have the following:

1. **Python 3.11+**  
   Install Python from the [https://www.python.org/](https://www.python.org/).

2. **Gurobi Optimizer**  
   - Download and install Gurobi from the [https://www.gurobi.com/](https://www.gurobi.com/).
   - Set up a valid Gurobi license. Please note free license may not be sufficient for large-scale models.

3. **Python Packages**  
   Install the required packages using pip:
   ```bash
   pip install gurobipy pandas openpyxl

---

## Usage

1. **Prepare the Data**  
   - Edit `data.xlsx` with the production data:
     - Production rate.
     - Yield rate.
     - Setup time.
     - Demand.

2. **Run the Model**  
   - Open the terminal and navigate to the repository folder.
   - Execute the `solver.py` script.
3. **View the Results**  
   - Check the console output.
   - Additional `result.xlsx` files, if generated, will appear in the same directory.
