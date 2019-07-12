---
layout: default
title: Quickstart
nav_order: 2
---

# Quickstart
{: .no_toc }

## Table of contents
{: .no_toc .text-delta }

1. TOC
{:toc}

---

## Solve a Continuous Problem

```python
import flippy

solver = flippy.GurobiSolver()

# 3 <= x <= 5, 0 <= y <= 10
x = flippy.LpVariable('x', up_bound=5, low_bound=3)
y = flippy.LpVariable('y', up_bound=10, low_bound=0)

# x + 2 = 3y + 4
lhs = flippy.LpExpression('lhs', {x:1}, constant=2)
rhs = flippy.LpExpression('rhs', {y:3}, constant=4) 
constraint = flippy.LpConstraint(lhs, 'eq', rhs)

# minimize: x + y => x = 3, y = 1/3
objective = flippy.LpObjective('test_obj', {x:1, y:1})
problem = flippy.LpProblem('test', objective, [constraint])
status = solver.solve(problem)
```

## Retrieve Results

After solving, a status is returned to indicate whether the solver has found a optimal solution for the problem. The values for the variables can be retrieved by `.evaluate()`.

```python
print(status)
# <SolutionStatus.Optimal: 1>
print(x.evaluate())
# 3.0
print(y.evaluate())
# 0.3333333333333333
```