import operator
import warnings

from flippy.lp_expression import LpExpression
from flippy.lp_variable import LpVariable


class LpConstraint:

    def __init__(self, lhs_expression, sense, rhs_expression=None,
                 name=None, slack=False, slack_penalty=0):
        self.lhs_expression = lhs_expression
        self.rhs_expression = rhs_expression or LpExpression()
        self.sense = sense
        self.name = name or ''
        self.slack = slack
        self.slack_penalty = slack_penalty

    @property
    def lhs_expression(self):
        return self._lhs_expression

    @lhs_expression.setter
    def lhs_expression(self, lhs_ex):
        if not isinstance(lhs_ex, LpExpression):
            raise ValueError('LHS of LpConstraint must be LpExpression')

        self._lhs_expression = lhs_ex

    @property
    def rhs_expression(self):
        return self._rhs_expression

    @rhs_expression.setter
    def rhs_expression(self, rhs_ex):
        if not isinstance(rhs_ex, LpExpression):
            raise ValueError('RHS of LpConstraint must be LpExpression')

        self._rhs_expression = rhs_ex

    @property
    def sense(self):
        return self._sense

    @sense.setter
    def sense(self, snse):
        if snse.lower() not in ('leq', 'eq', 'geq'):
            raise ValueError("Sense must be one of ('leq', 'eq', 'geq')")

        self._sense = snse.lower()

    @property
    def slack(self):
        return self._slack

    @slack.setter
    def slack(self, slck):
        if slck not in (True, False):
            raise ValueError('Slack indicator must be True or False')

        self._slack = slck

    def slack_variable(self):
        return (LpVariable(name=self.name + '_slack_variable',
                           var_type='Continuous',
                           low_bound=0) if self.slack else None)

    @property
    def slack_penalty(self):
        return self._slack_penalty

    @slack_penalty.setter
    def slack_penalty(self, sp):
        if sp < 0:
            raise ValueError('Slack penalty must be nonnegative')
        elif sp == 0 and self.slack:
            warnings.warn('Slack penalty is zero. No incentive to meet this constraint')

        self._slack_penalty = sp

    def check(self):
        return {'leq': operator.le,
                'eq': operator.eq,
                'geq': operator.ge}[self.sense](self.lhs_expression.evaluate(),
                                                self.rhs_expression.evaluate())
