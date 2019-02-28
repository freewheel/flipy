import pytest

from flippy.lp_problem import LpProblem
from flippy.objective import Objective
from flippy.lp_variable import LpVariable
from flippy.lp_expression import LpExpression


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
        pass
