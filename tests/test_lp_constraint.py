import pytest

from flipy.lp_constraint import LpConstraint
from flipy.lp_expression import LpExpression
from flipy.lp_variable import LpVariable, VarType


@pytest.fixture
@pytest.mark.usefixtures('x', 'y')
def lhs(x, y):
    # x + 3y + 7
    return LpExpression('lhs', {x: 1,
                                y: 3},
                        7)


@pytest.fixture
@pytest.mark.usefixtures('x', 'y')
def rhs(x, y):
    # x + 5y + 2
    return LpExpression('rhs', {x: 1,
                                y: 5},
                        2)


@pytest.fixture
@pytest.mark.usefixtures('lhs', 'rhs')
def lp_constraint(lhs, rhs):
    return LpConstraint(lhs,
                        'leq',
                        rhs,
                        'test_constraint')


@pytest.fixture
@pytest.mark.usefixtures('lhs', 'rhs')
def lp_constraint_with_slack(lhs, rhs):
    return LpConstraint(lhs,
                        'leq',
                        rhs,
                        'test_constraint',
                        True,
                        10.)


@pytest.mark.usefixtures('lhs', 'rhs', 'lp_constraint',
                         'lp_constraint_with_slack', 'x', 'y')
class TestLpConstraint:

    def test_init(self, lhs, rhs, lp_constraint):
        assert lp_constraint.lhs == lhs
        assert lp_constraint.rhs == rhs
        assert lp_constraint.sense == 'leq'
        assert lp_constraint.name == 'test_constraint'
        assert not lp_constraint.slack
        assert lp_constraint.slack_penalty == 0

    def test_init_no_rhs(self, lhs):
        lp_constraint = LpConstraint(lhs, 'leq')

        assert lp_constraint.rhs == LpExpression()

    def test_invalid_exprs(self, lhs):
        # test LHS
        with pytest.raises(ValueError) as e:
            LpConstraint('invalid', 'leq')

            assert 'lhs' in e.message.lower()

        # test RHS
        with pytest.raises(ValueError) as e:
            LpConstraint(lhs, 'leq', 'invalid')

            assert 'rhs' in e.message.lower()

    def test_invalid_sense(self, lhs):
        with pytest.raises(ValueError) as e:
            LpConstraint(lhs, 'invalid')

            assert 'sense' in e.message.lower()

        with pytest.raises(ValueError) as e:
            LpConstraint(lhs, 1)

            assert 'sense' in e.message.lower()

    def test_lower_bound(self, lhs, rhs):
        constraint = LpConstraint(lhs,
                                  'leq',
                                  rhs,
                                  'test_constraint')
        assert constraint.lower_bound is None
        assert constraint.upper_bound == -5

        constraint = LpConstraint(lhs,
                                  'geq',
                                  rhs,
                                  'test_constraint')
        assert constraint.upper_bound is None
        assert constraint.lower_bound == -5

        constraint = LpConstraint(lhs,
                                  'eq',
                                  rhs,
                                  'test_constraint')
        assert constraint.upper_bound == -5
        assert constraint.lower_bound == -5

    def test_breakdown(self, lhs, rhs):
        constraint = LpConstraint(lhs,
                                  'eq',
                                  rhs,
                                  'test_constraint')
        lower_bound_constraint, upper_bound_constraint = constraint.breakdown()
        assert lower_bound_constraint.sense == 'geq'
        assert lower_bound_constraint.name == 'test_constraint_lb'
        assert upper_bound_constraint.sense == 'leq'
        assert upper_bound_constraint.name == 'test_constraint_ub'

    def test_invalid_slack(self, lhs):
        with pytest.raises(ValueError) as e:
            LpConstraint(lhs, 'leq', slack='invalid')

            assert 'slack' in e.message.lower()

    def test_slack_variable(self, lp_constraint, lp_constraint_with_slack):
        assert lp_constraint.slack_variable is None

        slack_var = lp_constraint_with_slack.slack_variable

        assert isinstance(slack_var, LpVariable)
        assert slack_var.name.endswith('slack_variable')
        assert slack_var.var_type == VarType.Continuous
        assert slack_var.low_bound == 0

    def test_invalid_slack_penalty(self, lhs):
        with pytest.raises(ValueError) as e:
            LpConstraint(lhs, 'leq', slack_penalty=-1)

            assert 'slack penalty' in e.message.lower()

    def test_check(self, x, y, lhs, rhs):
        lp_constraint = LpConstraint(lhs, 'geq', rhs)
        x.set_value(5)
        y.set_value(0)

        assert lp_constraint.check()

        lp_constraint = LpConstraint(lhs, 'leq', rhs)

        assert not lp_constraint.check()

        lp_constraint.slack = True
        lp_constraint.slack_variable.set_value(100)

        assert lp_constraint.check()

        lp_constraint.slack = False
        assert not lp_constraint.check()

    def test_to_lp_terms(self, x, y):
        # 2x + 3y + 7
        lhs = LpExpression('lhs', {x: 2, y: 3}, 7)
        # x + 5y + 2
        rhs = LpExpression('rhs', {x: 1, y: 5}, 2)

        constraint = LpConstraint(lhs,
                                  'leq',
                                  rhs,
                                  'test_constraint')

        assert constraint.to_lp_terms() == ['x', '- 2 y', '<=', '-5']
