import pytest

from flipy.lp_problem import LpProblem
from flipy.lp_objective import LpObjective, Maximize
from flipy.lp_variable import LpVariable, VarType
from flipy.lp_expression import LpExpression
from flipy.lp_constraint import LpConstraint

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
        objective = LpObjective(name='minimize_cpm', expression={x: 998}, constant=8)
        problem.set_objective(objective)
        assert problem.lp_objective == objective

        with pytest.raises(Exception) as e:
            problem.set_objective(objective)
        assert e.value.args == ('LP objective is already set',)
        assert x.obj_coeff == 998

        with pytest.raises(Exception) as e:
            problem.set_objective('invalid')
        assert e.value.args == ('invalid is not an LpObjective',)

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
        objective = LpObjective(name='minimize_cpm', expression={x: 998}, constant=8)
        rhs = LpExpression('rhs', {x: 1})
        lhs = LpExpression('lhs', {}, -2)
        constraint = LpConstraint(rhs, 'geq', lhs, 'constraint')
        problem.add_constraint(constraint)
        problem.set_objective(objective)
        buffer = StringIO()
        problem.write_lp(buffer)
        flipy_string = buffer.getvalue()
        assert flipy_string == '\\* test_problem *\\\nMinimize\nminimize_cpm: 998 x + 8\nSubject To\nconstraint: x >= -2\nBounds\nx <= 10\nEnd'

    def test_write_slack(self, problem, x):
        objective = LpObjective(name='minimize_cpm', expression={x: 998}, constant=8, sense=Maximize)
        rhs = LpExpression('rhs', {x: 1})
        lhs = LpExpression('lhs', {}, -2)
        constraint = LpConstraint(rhs, 'leq', lhs, 'constraint', True, 100)
        problem.add_constraint(constraint)
        problem.set_objective(objective)
        buffer = StringIO()
        problem.write_lp(buffer)
        flipy_string = buffer.getvalue()
        assert flipy_string == '\\* test_problem *\\\nMaximize\nminimize_cpm: 998 x - 100 constraint_slack_variable + 8\nSubject To\nconstraint: - constraint_slack_variable + x <= -2\nBounds\nx <= 10\nEnd'

    def test_write_with_empty_constraint(self, problem, x):
        objective = LpObjective(name='minimize_cpm', expression={x: 998}, constant=8, sense=Maximize)
        constraint = LpConstraint(LpExpression('lhs', {x: 0}), 'leq', LpExpression('rhs', {}), 'constraint')
        problem.add_constraint(constraint)
        problem.set_objective(objective)
        buffer = StringIO()
        problem.write_lp(buffer)
        flipy_string = buffer.getvalue()
        assert flipy_string == '\\* test_problem *\\\nMaximize\nminimize_cpm: 998 x + 8\nSubject To\nBounds\nx <= 10\nEnd'

    def test_write_long(self, problem, x):
        a = LpVariable('a', low_bound=0, up_bound=10, var_type=VarType.Integer)
        b = LpVariable('b', low_bound=0, up_bound=10, var_type=VarType.Integer)
        c = LpVariable('c', low_bound=0, up_bound=10, var_type=VarType.Integer)
        d = LpVariable('d', low_bound=0, up_bound=10, var_type=VarType.Integer)
        e = LpVariable('e', var_type=VarType.Binary)
        f = LpVariable('f', var_type=VarType.Binary)
        g = LpVariable('g', var_type=VarType.Binary)
        h = LpVariable('h', var_type=VarType.Binary)
        vars = [a, b, c, d, e, f, g, h]

        # make sure objective is long enough to test the line break
        objective = LpObjective(name='minimize_cpm', expression={v: 3.1415926535 for v in vars}, constant=8)

        rhs = LpExpression('rhs', {a: 1000, b: 1000, c: 1000, d: 1000})
        lhs = LpExpression('lhs', {}, -2)
        constraint = LpConstraint(rhs, 'geq', lhs, 'constraint')

        problem.add_constraint(constraint)
        problem.set_objective(objective)
        buffer = StringIO()
        problem.write_lp(buffer)
        lp_str = buffer.getvalue()
        assert lp_str.split('\n') == [
            '\\* test_problem *\\',
            'Minimize',
            'minimize_cpm: 3.1415926535 a + 3.1415926535 b + 3.1415926535 c + 3.1415926535 d',
            '+ 3.1415926535 e + 3.1415926535 f + 3.1415926535 g + 3.1415926535 h + 8',
            'Subject To',
            'constraint: 1000 a + 1000 b + 1000 c + 1000 d >= -2',
            'Bounds',
            '0 <= a <= 10',
            '0 <= b <= 10',
            '0 <= c <= 10',
            '0 <= d <= 10',
            '0 <= e <= 1',
            '0 <= f <= 1',
            '0 <= g <= 1',
            '0 <= h <= 1',
            'Generals',
            'a',
            'b',
            'c',
            'd',
            'Binaries',
            'e',
            'f',
            'g',
            'h',
            'End'
        ]

    def test_write_no_objective(self, problem, x):
        rhs = LpExpression('rhs', {x: 1})
        lhs = LpExpression('lhs', {}, -2)
        constraint = LpConstraint(rhs, 'geq', lhs, 'constraint')
        problem.add_constraint(constraint)
        buffer = StringIO()

        with pytest.raises(Exception) as e:
            problem.write_lp(buffer)
        assert e.value.args == ('No objective',)
