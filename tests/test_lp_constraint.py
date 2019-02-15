import pytest

from flippy.lp_constraint import LpConstraint
from flippy.lp_expression import LpExpression


@pytest.fixture
@pytest.mark.usefixtures('x', 'y')
def lhs_expression(x, y):
    # x + 3y + 7
    return LpExpression('lhs', {x: 1,
                                y: 3},
                        7)


@pytest.fixture
@pytest.mark.usefixtures('x', 'y')
def rhs_expression(x, y):
    # x + 5y + 2
    return LpExpression('rhs', {x: 1,
                                y: 5},
                        2)


@pytest.fixture
@pytest.mark.usefixtures('lhs_expression', 'rhs_expression')
def lp_constraint(lhs_expression, rhs_expression):
    return LpConstraint(lhs_expression,
                        'leq',
                        rhs_expression,
                        'test_constraint')


@pytest.mark.usefixtures('lhs_expression', 'rhs_expression', 'lp_constraint')
class TestLpConstraint:

    def test_init(self, lhs_expression, rhs_expression, lp_constraint):
        assert lp_constraint.lhs_expression == lhs_expression
        assert lp_constraint.rhs_expression == rhs_expression
        assert lp_constraint.sense == 'leq'
        assert lp_constraint.name == 'test_constraint'
        assert not lp_constraint.slack
        assert lp_constraint.slack_penalty == 0

    def test_init_no_rhs(self, lhs_expression):
        lp_constraint = LpConstraint(lhs_expression, 'leq')

        assert lp_constraint.rhs_expression == LpExpression()

    def test_invalid_exprs(self, lhs_expression):
        # test LHS
        with pytest.raises(ValueError) as e:
            LpConstraint('invalid', 'leq')

            assert 'LHS' in e.message

        # test RHS
        with pytest.raises(ValueError) as e:
            LpConstraint(lhs_expression, 'leq', 'invalid')

            assert 'RHS' in e.message

    def test_invalid_sense(self, lhs_expression):
        with pytest.raises(ValueError) as e:
            lp_constraint(lhs_expression, 'invalid')

            assert 'Sense' in e.message
