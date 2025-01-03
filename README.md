# production-scheduling-case
This project contains a linearized Mixed-Integer Programming (MIP) model designed to solve production scheduling problems using the Gurobi optimizer.

The linearization is achieved by introducing auxiliary variables and indicator variables to replace non-linear expressions like conditional inequation and absolute value, ensuring the model is computationally efficient and suitable for optimization.

This model is based on the case presented in the following article:

B. Madhu Rao, Jeroen Beliën (2014) Case—Production Scheduling at Falcon Die Casting. INFORMS Transactions on Education 15(1):154-155. [https://doi.org/10.1287/ited.2014.0132cs](https://doi.org/10.1287/ited.2014.0132cs)

## Overview
The MIP model addresses the following key components of production scheduling:

### 1. Parameters
- $P_{ij}$: Production rate of part $j$ on machine $i$.  
- $Y_j$: Yield rate of part $j$.  
- $S_{ij}$: Setup time of machine $i$ for part $j$.  
- $D_{jk}$: Demand of part $j$ in week $k$.  

### 2.Variables
**Production-dependent**
- $n_{ijk}$: Amount of part $j$ to be produced on machine $i$ in week $k$.
- $b_{ijk}$: Indicate whether to produce part $j$ on machine $i$ in week $k$.

$$n_{ijk} \geq 0, \quad n_{ijk} \in \mathbb{Z}, \quad \forall i, j, k$$
$$b_{ijk} \in \\{ 0, 1 \\}, \quad \forall i, j, k$$

**Inventory-dependent**
- $p_{jk}$: Amount of part $j$ not delivered on time in week $k$.
- $t_{jk}$: Amount of part $j$ in stock in week $k$.

$$p_{jk}, t_{jk} \geq 0, \quad p_{jk}, t_{jk} \in \mathbb{Z},  \quad \forall j, k$$

**Time-dependent**
- $h_{ik}$: Duration of machine $i$ operating in week $k$.
- $v_{ik}$: Duration of overtime of machine $i$ operating in week $k$.
- $e_{ik}$: Duration exceeding maximum overtime of machine $i$ operating in week $k$.
- $w_k$: Max duration among all machines operating in week $k$.

$$h_{ik}, v_{ik}, e_{ik}  \geq 0,  \quad \forall i, k$$
$$w_k \geq 0,  \quad \forall k$$

**Setup-dependent**
- $c_{ijk}$: Indicate whether to initially setup on machine $i$ to produce $j$ in week $k$.
- $c_{ijk}^+$: Value of positive variation of $c_{ijk}$ between consecutive weeks.
- $c_{ijk}^-$: Value of negative variation of $c_{ijk}$ between consecutive weeks.
- $a_{ijk}$: Indicate whether to compute setup time on machine $i$ to produce $j$ in week $k$.
- $x_{ik}$: Indicate the variation in setup time affected by the number of types of parts produced on machine $i$ in week $k$.

$$c_{ijk}, c_{ijk}^+, c_{ijk}^-, a_{ijk} \in \\{ 0, 1 \\},  \quad \forall i, j, k$$
$$x_{ik} \in \\{ 0, 1 \\},  \quad \forall i, k$$

### 3. Constraints
**Production-dependent**
- Production only takes place when it is scheduled.

$$n_{ijk} \leq M \cdot b_{ijk}, \quad \forall i, j, k$$

- Total production meets the total demand.

$$\sum_k \sum_i n_{ijk} \geq \sum_k D_{kj}, \quad \forall j, k$$

**Inventory-dependent**
- Backlog from the previous week is carried over into the current week, while the stock from the previous week satisfies the demand for the current week.

$$\sum_i n_{ijk} + p_{jk} + t_{j(k-1)} \geq D_{kj} + p_{j(k-1)} + t_{jk}, \quad \forall j, k \neq \text{first, last}$$

- There is no backlog or stock before the first week.

$$\sum_i n_{ijk} + p_{jk} \geq D_{kj} + t_{jk}, \quad \forall j, k = \text{first}$$

- There is no backlog or stock in the last week.

$$\sum_i n_{ijk} + t_{j(k-1)} \geq D_{kj} + p_{j(k-1)}, \quad \forall j, k = \text{last}$$

**Time-dependent**
- Total working time is required for production and setup.

$$\sum_j \left( \frac{n_{ijk}}{P_{ij} \cdot Y_j} + S_{ij} \cdot a_{ijk} \right) \leq h_{ik}, \quad \forall i, k$$

- Overtime begins when working time exceeds regular hours.

$$v_{ik} \geq h_{ik} - 120, \quad \forall i, k$$

- Overtime exceeding maximum allowable extra hours leads to infeasible solution.

$$v_{ik} \leq 48 + e_{ik}, \quad \forall i, k$$

- Weekly maximum overtime covers all machine overtime.

$$w_k \geq v_{ik}, \quad \forall i, k$$

**Setup-dependent**
- Setup time is adjusted based on initial setup.

$$a_{ijk} \geq b_{ijk} - c_{ijk}, \quad \forall i, j, k$$

- Only one is initially setup among all machines in a given week.

$$\sum_j c_{ijk} = 1, \quad \forall i, k$$

- Initial setup depends on prior production.

$$c_{ijk} \leq b_{ij(k-1)}, \quad \forall i, j, k$$

- Variation is computed in setup status between consecutive weeks.

$$c_{ijk}^+ - c_{ijk}^- = c_{ijk} - c_{ij(k-1)}, \quad \forall i, j, k$$

- Variation is limited in setup status.

$$c_{ijk}^+ + c_{ijk}^- \leq 1, \quad \forall i, j, k$$

- Variation in setup status is matched to the number of types of parts to be produced.

$$\sum_j b_{ijk} \leq 1 + M \cdot x_{ik}, \quad \forall i, k$$

$$\sum_j b_{ijk} \geq 2 - M \cdot x_{ik}, \quad \forall i, k$$

$$\sum_j \left( c_{ijk}^+ + c_{ijk}^- \right) = 2 \cdot x_{ik}, \quad \forall i, k$$

**_For detailed explanations of above constraints, please refer to the Linearization section._**

### 4. Objective Functions
The objective function balances production scheduling and resource utilization to minimize the costs associated with machine maintaining cost( $\\alpha$ ) and personnel operating cost( $\\beta$ ), backlog penalties( $\\gamma$ ) and inventory cost( $\\delta$ ). The weighted constants allow for fine-tuning the relative importance of each factor in the overall optimization process.

$$\min M \sum_k \sum_i e_{ik} + \alpha \sum_k w_k + \beta \sum_k \sum_i v_{ik} + \gamma \sum_k \sum_j p_{jk} + \delta \sum_k \sum_j t_{jk}$$

## Linearization
To determine which part a machine is initially setup to produce in a given week, it is essential to account for the variation in setup status between consecutive weeks. There exists a non-linear relationship between $b_{ijk}$ and $c_{ijk}$. To enhance the model's efficiency, linearization is essential, as directly solving a non-linear model using the Gurobi Optimizer is computationally expensive.

- Case 1: If a machine produces only one part in the previous week, the initial setup in the current week remains unchanged.

<div align="center">

|        | $b_{ij(k-1)}$ | $b_{ijk}$ | $c_{ij(k-1)}$ | $c_{ijk}$ | $\Delta c_{ijk}$ |
|:------:|:-------------:|:---------:|:-------------:|:---------:|:----------------:|
| Part 1 | 1             | 0         | 1             | 1         | 0                |
| Part 2 | 0             | 1         | 0             | 0         | 0                |
| Part 3 | 0             | 0         | 0             | 0         | 0                |
| **$\sum_j \Delta c_{ijk}$** | |    |               |           | **0**            |

</div>

- **Case 2**: If a machine produces more than one part in the previous week, the initial setup in the current week differst from that in the previous week.

<div align="center">

|        | $b_{ij(k-1)}$ | $b_{ijk}$ | $c_{ij(k-1)}$ | $c_{ijk}$ | $\Delta c_{ijk}$ |
|:------:|:-------------:|:---------:|:-------------:|:---------:|:----------------:|
| Part 1 | 1             | 0         | 1             | 0         | 1                |
| Part 2 | 1             | 1         | 0             | 1         | 1                |
| Part 3 | 0             | 1         | 0             | 0         | 0                |
| **$\sum_j \Delta c_{ijk}$** | |    |               |           | **2**            |

</div>

The two cases outlined describe how the setup of a machine in the current week depends on the number of parts it produced in the previous week.

$$\sum_j b_{ij(k-1)} \leq 1 \iff \sum_j |c_{ijk} - c_{ij(k-1)}| = 0$$

$$\sum_j b_{ij(k-1)} \geq 2 \iff \sum_j |c_{ijk} - c_{ij(k-1)}| = 2$$

To move towards linearizing the non-linear relationships in the current model, auxiliary variables $c_{ijk}^+, c_{ijk}^-$ and indicator variable $x_{ijk}$ are introduced to linearize the absolute value expression of $c_{ijk}$ at the right-hand side and the inequation of $b_{ijk}$ at the left-hand side respectievly.

### Absolute value
The following constraint is introduced to enforce the relationship between the setup values.

$$c_{ijk}^+ - c_{ijk}^- = c_{ijk} - c_{ij(k-1)}, \quad \forall i, j, k$$

such that the absolute value is replaced.

$$|c_{ijk} - c_{ij(k-1)}| = c_{ijk}^+ + c_{ijk}^-, \quad \forall i, j, k$$

The table below illustrates all possible values.

<div align="center">

| $c_{ijk} - c_{ij(k-1)}$ | $c_{ijk}^+ - c_{ij(k-1)}^-$ | value | $c_{ijk}^+ + c_{ij(k-1)}^-$ | value |
|:-----------------------:|:---------------------------:|:-----:|:-------------------------:|:-----:|
| 1 - 1                   | ~~1 - 1~~ or 0 - 0          | 0     | ~~1 + 1~~ or 0 + 0           | 0     |
| 1 - 0                   | 1 - 0                       | 1     | 1 + 0                       | 1     |
| 0 - 1                   | 0 - 1                       | -1    | 0 + 1                       | 1     |
| 0 - 0                   | ~~1 - 1~~ or 0 - 0          | 0     | ~~1 + 1~~ or 0 + 0           | 0     |

</div>

There exists an infeasible case where both $c_{ijk}^+$ and $c_{ij(k-1)}^-$ cannot be equal to 1 simultaneously.To prevent this, the following constraint is introduced.

$$c_{ijk}^+ + c_{ijk}^- \leq 1, \quad \forall i, j, k$$

### Conditional Inequation
The variable $x_{ijk}$ serves to capture the relationship between $b_{ijk}$ and $c_{ijk}$. The following constraints define this relationship.

$$\sum_j b_{ijk} \leq 1 + M \cdot x_{ik}, \quad \forall i, k$$

$$\sum_j b_{ijk} \geq 2 - M \cdot x_{ik}, \quad \forall i, k$$

$$\sum_j \left( c_{ijk}^+ + c_{ijk}^- \right) = 2 \cdot x_{ik}, \quad \forall i, k$$

The table below shows these two cases.

<div align="center">

| $x_{ijk}$ | $\sum_j b_{ijk}$ | $c_{ijk}^+ - c_{ijk}^-$ |
|:---------:|:----------------:|:-----------------------:|
| 0         | $\leq 1$         | 0                       |
| 1         | $\geq 2$         | 2                       |

</div>

## Requirements
To run the MIP model, ensure you have the following:

**1. Python 3.11+**  
   - Install Python from the [https://www.python.org/](https://www.python.org/).

**2. Gurobi Optimizer**  
   - Download and install Gurobi from the [https://www.gurobi.com/](https://www.gurobi.com/).
   - Set up a valid Gurobi license. Please note that free license may not be sufficient for large-scale models.

**3. Python Packages**  
   - Install the required packages using pip.
   ```bash
   pip install gurobipy pandas openpyxl
   ```

## Usage
**1. Prepare the Data**  
   - Edit `data.xlsx` with the production data:
     - Production rate.
     - Yield rate.
     - Setup time.
     - Demand.
     - Cost(weight and priority).

**2. Run the Model**  
   - Open the terminal and navigate to the repository folder.
   - Execute the `solver.py` script.

**3. View the Results**  
   - Check the console output.
   - Additional `result.xlsx` files containing values ​​of decision variables, if generated, will appear in the same directory.
