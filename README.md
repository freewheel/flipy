# Flipy

![flipy_logo_60pt](https://github.freewheel.tv/storage/user/281/files/c52c2900-a42d-11e9-805f-97a426a5d2d8)

Flipy is a Python linear programming interface library, originall developed by [FreeWheel](https://freewheel.com). It currently supports Gurobi and CBC as the backend solver.

To use CBC, follow the [CBC documentation here](https://github.com/coin-or/Cbc#building-from-source) and make sure the command cbc is available on your machine.

To use Gurobi, make sure you have a Gurobi license file, and gurobipy is installed in your Python environment. You can find details from [Gurobi’s documentation](https://www.gurobi.com/documentation/8.1/quickstart_mac/the_gurobi_python_interfac.html).

Flipy requires Python 3.6 or newer.

## Installation

Flipy can be installed with `setuptools`.

```
$ git clone https://github.freewheel.tv/linear/flipy
$ cd flipy
$ python setup.py install
```

## Quickstart

Here is a simple example for Flipy:

```python
import flipy

solver = flipy.GurobiSolver()

# 3 <= x <= 5, 0 <= y <= 10
x = flipy.LpVariable('x', up_bound=5, low_bound=3)
y = flipy.LpVariable('y', up_bound=10, low_bound=0)

# x + 2 = 3y + 4
lhs = flipy.LpExpression('lhs', {x: 1}, constant=2)
rhs = flipy.LpExpression('rhs', {y: 3}, constant=4) 
constraint = flipy.LpConstraint(lhs, 'eq', rhs)

# minimize: x + y => x = 3, y = 1/3
objective = flipy.LpObjective('test_obj', {x: 1, y: 1})
problem = flipy.LpProblem('test', objective, [constraint])
status = solver.solve(problem)
```

After solving, a status is returned to indicate whether the solver has found a optimal solution for the problem. The values for the variables can be retrieved by `.evaluate()`.

```python
print(status)
# <SolutionStatus.Optimal: 1>
print(x.evaluate())
# 3.0
print(y.evaluate())
# 0.3333333333333333
```
