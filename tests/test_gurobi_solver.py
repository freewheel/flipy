import pytest
from flippy.lp_problem import LpProblem
from flippy.lp_constraint import LpConstraint
from flippy.lp_expression import LpExpression
from flippy.lp_variable import LpVariable, VarType
from flippy.lp_objective import LpObjective
from flippy.solvers.gurobi_solver import GurobiSolver, SolutionStatus
import math


@pytest.fixture
def solver():
    return GurobiSolver()


class TestGurobiSolver:
    def test_solvable_continuous(self, solver):
        # 3 <= x <= 5, 0 <= y <= 10
        # x + 2 = 3y + 4
        # minimize: x + y => x = 3, y = 1/3
        x = LpVariable('x', up_bound=5, low_bound=3)
        y = LpVariable('y', up_bound=10, low_bound=0)
        lhs = LpExpression('lhs', {x: 1}, constant=2)
        rhs = LpExpression('rhs', {y: 3}, constant=4)
        constraint = LpConstraint(lhs, 'eq', rhs)
        objective = LpObjective('test_obj', {x: 1, y: 1})
        problem = LpProblem('test', objective, [constraint])
        status = solver.solve(problem)
        assert status == SolutionStatus.Optimal
        assert x._value == 3
        assert math.isclose(y._value, 1.0 / 3)
        
    def test_solvable_integer(self, solver):
        # 3 <= x <= 5, 0 <= y <= 10 (x, y are integers)
        # x + 2 = 3y + 4
        # minimize: x + y => x = 5, y = 1
        x = LpVariable('x', var_type=VarType.Integer, up_bound=5, low_bound=3)
        y = LpVariable('y', var_type=VarType.Integer, up_bound=10, low_bound=0)
        lhs = LpExpression('lhs', {x:1}, constant=2)
        rhs = LpExpression('rhs', {y:3}, constant=4) 
        constraint = LpConstraint(lhs, 'eq', rhs)
        objective = LpObjective('test_obj', {x:1, y:1})
        problem = LpProblem('test', objective, [constraint])
        status = solver.solve(problem)
        assert status == SolutionStatus.Optimal
        assert x._value == 5
        assert y._value == 1

    def test_infeasible(self, solver):
        # 0 <= x <= 1, 0 <= y <= 1 (x, y are binarys)
        # x + 2 = 3y + 4
        # minimize: x + y => Infeasible
        x = LpVariable('x', var_type=VarType.Binary)
        y = LpVariable('y', var_type=VarType.Binary)
        lhs = LpExpression('lhs', {x:1}, constant=2)
        rhs = LpExpression('rhs', {y:3}, constant=4) 
        constraint = LpConstraint(lhs, 'eq', rhs)
        objective = LpObjective('test_obj', {x:1, y:1})
        problem = LpProblem('test', objective, [constraint])
        status = solver.solve(problem)
        assert status == SolutionStatus.Infeasible
