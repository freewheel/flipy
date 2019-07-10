import pytest

from flippy.lp_problem import LpProblem
from flippy.objective import Objective
from flippy.lp_variable import LpVariable
from flippy.lp_expression import LpExpression
from flippy.lp_constraint import LpConstraint

import pulp
from io import StringIO


@pytest.fixture
def problem():
    return LpProblem('test_problem')


@pytest.fixture
def expression(x):
    return LpExpression(name='test_expr', expression={x: 998}, constant=8)


@pytest.mark.usefixtures('problem', 'x')
class TestLpProblem(object):

    def test_init(self):
        problem = LpProblem('test_problem')
        assert problem.lp_objective is None
        assert len(problem.lp_constraints) == 0 and isinstance(problem.lp_constraints, dict)
        assert len(problem.lp_variables) == 0 and isinstance(problem.lp_variables, dict)

    def test_add_variable(self, problem, x):
        problem.add_variable(x)
        assert problem.lp_variables == {'x': x}

        with pytest.raises(Exception) as e:
            problem.add_variable('123')
        assert e.value.args == ('123 is not an LpVariable',)

        x2 = LpVariable('x')
        with pytest.raises(Exception) as e:
            problem.add_variable(x2)
        assert e.value.args == ('LP variable name x conflicts with an existing LP variable',)

    def test_set_objective(self, problem, x):
        objective = Objective(name='minimize_cpm', expression={x: 998}, constant=8)
        problem.set_objective(objective)
        assert problem.lp_objective == objective

        with pytest.raises(Exception) as e:
            problem.set_objective(objective)
        assert e.value.args == ('LP objective is already set',)

    def test_add_constraint(self, problem, x):
        rhs = LpExpression('rhs', {x: 1})
        lhs = LpExpression('lhs', {x: 1}, 2)
        constraint = LpConstraint(rhs, 'geq', lhs, 'constraint')
        problem.add_constraint(constraint)

        assert problem.lp_constraints[constraint.name] == constraint
        assert problem.lp_variables[x.name] == x

        constraint = LpConstraint(lhs, 'geq', rhs, 'constraint')
        with pytest.raises(Exception) as e:
            problem.add_constraint(constraint)
        assert e.value.args == ('LP constraint name %s conflicts with an existing LP constraint' % constraint.name,)

        with pytest.raises(Exception) as e:
            problem.add_constraint(10)
        assert e.value.args == ('%s is not an LpConstraint' % 10,)

    def test_write(self, problem, x):
        objective = Objective(name='minimize_cpm', expression={x: 998}, constant=8)
        rhs = LpExpression('rhs', {x: 1})
        lhs = LpExpression('lhs', {}, -2)
        constraint = LpConstraint(rhs, 'geq', lhs, 'constraint')
        problem.add_constraint(constraint)
        problem.set_objective(objective)
        buffer = StringIO()
        problem.writeLP(buffer)
        flippy_string = buffer.getvalue()
        assert flippy_string == '\\* test_problem *\\\nMinimize\nminimize_cpm: 998 x\nSubject To\nconstraint: x >= -2\nBounds\nx <= 10\nEnd\n'

        problem2 = pulp.LpProblem(sense=pulp.LpMinimize, name='test_problem')
        x2 = pulp.LpVariable('x', lowBound=0, upBound=10)
        constr = x2 >= -2
        constr.name = 'constraint'
        problem2 += constr
        obj = 998 * x2 + 8
        problem2 += obj
        problem2.objective.name = 'minimize_cpm'
        filename2 = 'tests/test_output/test_gurobi.lp'
        problem2.writeLP(filename2)

        with open(filename2, 'r') as f:
            assert ''.join(f.readlines()) == flippy_string
