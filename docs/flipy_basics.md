---
layout: default
title: Flipy Basics
nav_order: 3
---

# Flipy basics
{: .no_toc }

## Table of contents
{: .no_toc .text-delta }

1. TOC
{:toc}

---

## Variable

Create a variable with `flipy.LpVariable`:

```python
x = flipy.LpVariable('x', low_bound=1, up_bound=5)
```

By default, variables are created as continous type, meaning it can take any value between its lower and upper bound.

Integer and binary variable types are also available:

```python
y = flipy.LpVariable('y', var_type=flipy.VarType.Integer, low_bound=1, up_bound=5)
z = flipy.LpVariable('y', var_type=flipy.VarType.Binary)
```

`y` can take any integer value from 1 to 5 (1, 2, 3, 4, 5), while `z` can only take 0 or 1.


## Expression

An LP expression is a mapping from variables to coefficients, with an optional constant.

$$
3x + 2y + 5
$$

For example, the above LP expression can be created by:

```python
expr = flipy.LpExpression(expression={x: 3, y: 2}, constant=5)
```

## Constraint

A constraint has 3 compontents: `lhs`, `sense` and `rhs`.

1. `lhs`: The left-hand side expression of the constraint
2. `sense`: The sense of the constraint, can be one of:
    1. `leq`: The left-hand side expression must be less than or equal to the right hand side expression
    2. `eq`: The left-hand side expression must be equal to the right hand side expression
    2. `geq`: The left-hand side expression must be greater than or equal to the right hand side expression
3. `rhs`: The right-hand side expression of the constraint

$$
x <= y + 10
$$

For example, the above constraint can be created by:

```python
lhs = flipy.LpExpression(expression={x: 1})
rhs = flipy.LpExpression(expression={y: 2}, constant=10)
cons = flipy.LpConstraint(lhs, 'leq', rhs)
```

## Objective

The purpose of linear programming is to find the optimal values of the variables that maximize or minimize the objective function. An objective function defines the numeric value that we want to optimize. 

In flipy, an objective function is an expression with a sense indicator. The sense indicator can be either `flipy.Minimize` or `flipy.Maximize`.

To create an objective function:

```python
obj = flipy.LpObjective(expression={x: 3, y: 2}, constant=5, sense=flipy.Maximize)
```

## Problem

To create a problem, we need to provide the objective and the constraints:

```python
problem = flipy.LpProblem('test_problem', lp_objective=obj, lp_constraints=[cons])
```

We can also create an empty problem and add the objective function and constraints later

```python
problem = flipy.LpProblem('test_problem')
problem.add_constraint(cons)
problem.set_objective(obj)
```

## Solving

Flipy currently supports two linear solver: [CBC](https://github.com/coin-or/Cbc) and [Gurobi](https://gurobi.com)

To solve a problem, create a solver instance first:

```python
solver = flipy.CBCSolver()
```

Solve the created problem:

```python
status = solver.solve(problem)
```

`status` is the 
There are 4 possible status codes:

1. `flipy.SolutionStatus.Optimal`: The solver has succesfully solved the problem and an optimal solution is returned
2. `flipy.SolutionStatus.Infeasible`: The solver couldn't find a solution for the problem as there is no feasible region
2. `flipy.SolutionStatus.Unbounded`: The solver couldn't find a solution for the problem as the feasible region is unbouned and the objective function is infinite
2. `flipy.SolutionStatus.NotSolved`: An error has occurred and the problem is not solved

To retrieve the values of the variables, call `LpVariable.evaluate`:

```python
val_x = x.evaluate()
val_y = y.evaluate()
```

To get the value of objective function: call `LpObjective.evalaute()`:

```python
val_obj = obj.evaluate()
```
