import operator
import warnings

from flippy.lp_expression import LpExpression
from flippy.lp_variable import LpVariable, VarType
from flippy.utils import LpCplexLPLineSize, _count_characters


class LpConstraint:

    def __init__(self, lhs_expression, sense, rhs_expression=None,
                 name=None, slack=False, slack_penalty=0):
        self.lhs_expression = lhs_expression
        self.rhs_expression = rhs_expression or LpExpression()
        self.sense = sense
        self.name = name or ''
        self.slack = slack
        self.slack_penalty = slack_penalty

        self._slack_variable = None

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
        try:
            assert snse.lower() in ('leq', 'eq', 'geq')
            self._sense = snse.lower()
        except (AttributeError, AssertionError):
            raise ValueError("Sense must be one of ('leq', 'eq', 'geq')")

    @property
    def lower_bound(self):
        if self.sense == 'leq':
            return None
        return self.rhs_expression.const - self.lhs_expression.const

    @property
    def upper_bound(self):
        if self.sense == 'geq':
            return None
        return self.rhs_expression.const - self.lhs_expression.const

    @property
    def slack(self):
        return self._slack

    @slack.setter
    def slack(self, slck):
        if slck not in (True, False):
            raise ValueError('Slack indicator must be True or False')

        self._slack = slck

    @property
    def slack_variable(self):
        self._slack_variable = (self._slack_variable or LpVariable(name=self.name + '_slack_variable',
                                                                  var_type=VarType.Continuous,
                                                                  low_bound=0)) if self.slack else None
        return self._slack_variable

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

    def asCplexLpConstraint(self, name):
        """
        Returns a constraint as a string
        """
        lhs_result, line = self.lhs_expression.asCplexVariablesOnly(name)
        if self.lhs_expression.const:
            if self.lhs_expression.const < 0:
                term = " - %s" % (-self.lhs_expression.const)
            elif self.lhs_expression.const > 0:
                term = " + %s" % self.lhs_expression.const
            line += [term]

        if not list(self.lhs_expression.expr.keys()):
            line += ["0"]
        if self.sense.lower() == 'leq':
            sense = '<='
        elif self.sense.lower() == 'geq':
            sense = '>='
        else:
            sense = '='

        rhs_result, rhs_line = self.rhs_expression.asCplexVariablesOnly(name)

        # Could probably do some better checks on line length when trying to do combining
        if not list(self.rhs_expression.expr.keys()) and not self.rhs_expression.const:
            rhs_line += ["0"]

        # Note this does not check the length
        # If variables exist
        if list(self.rhs_expression.expr.keys()):
            if self.rhs_expression.const < 0:
                term = " - %s" % (-self.rhs_expression.const)
            elif self.rhs_expression.const > 0:
                term = " + %s" % self.rhs_expression.const
            rhs_line += [term]
        else:
            term = str(self.rhs_expression.const)
            rhs_line += [term]

        term = " %s %s" % (sense, rhs_result[0][1:] if rhs_result else "".join(rhs_line[1:]) if rhs_line else '')
        if _count_characters(line)+len(term) > LpCplexLPLineSize:
            lhs_result += ["".join(line)]
            line = [term]
        else:
            line += [term]
        lhs_result += ["".join(line)]

        if rhs_result:
            lhs_result += ["".join(rhs_line)]

        result = "%s\n" % "\n".join(lhs_result)
        return result
