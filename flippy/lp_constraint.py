import copy
import operator
import warnings
from typing import Optional

from flippy.lp_expression import LpExpression
from flippy.lp_variable import LpVariable, VarType
from flippy.utils import LpCplexLPLineSize, _count_characters, Numeric


class LpConstraint:
    """ A class representing a linear constraint """

    def __init__(self, lhs_expression: LpExpression, sense: str, rhs_expression: Optional[LpExpression] = None, name:
                 Optional[str] = None, slack: bool = False, slack_penalty: Numeric = 0, copy_expr: bool = False) -> None:
        """ Initialize the constraint

        Parameters
        ----------
        lhs_expression:
            The left-hand-side expression
        sense:
            The type of constraint (leq, geq, or eq)
        rhs_expression:
            The right-hand-side expression
        name:
            The name of the constraint
        slack:
            Whether the constraint has slack
        slack_penalty:
            The penalty for the slack in the constraint
        copy_expr:
            Whether to copy the lhs and rhs expressions
        """
        self.lhs_expression = lhs_expression if not copy_expr else copy.copy(lhs_expression)
        if rhs_expression:
            self.rhs_expression = rhs_expression if not copy_expr else copy.copy(rhs_expression)
        else:
            self.rhs_expression = LpExpression()
        self.sense = sense
        self.name = name or ''
        self.slack = slack
        self.slack_penalty = slack_penalty

        self._slack_variable = None

        self._shift_variables_left()
        self._shift_constant_right()

    def _shift_variables_left(self) -> None:
        """ Moves all variables on rhs to lhs """
        if not self.rhs_expression.expr:
            return
        for var, coeff in self.rhs_expression.expr.items():
            self.lhs_expression.expr[var] -= coeff
        self.rhs_expression.expr.clear()

    def _shift_constant_right(self) -> None:
        """ Moves the constant on the lhs to the rhs """
        if not self.lhs_expression.const:
            return
        self.rhs_expression.const -= self.lhs_expression.const
        self.lhs_expression.const = 0

    @property
    def lhs_expression(self) -> LpExpression:
        """ Getter for lhs expression """
        return self._lhs_expression

    @lhs_expression.setter
    def lhs_expression(self, lhs_ex: LpExpression) -> None:
        """ Setter for lhs expression

        Parameters
        ----------
        lhs_ex:
            The lhs expression to set
        """
        if not isinstance(lhs_ex, LpExpression):
            raise ValueError('LHS of LpConstraint must be LpExpression')

        self._lhs_expression = lhs_ex  # pylint: disable=W0201

    @property
    def rhs_expression(self) -> LpExpression:
        """ Getter for rhs expression """
        return self._rhs_expression

    @rhs_expression.setter
    def rhs_expression(self, rhs_ex: LpExpression) -> None:
        """ Setter for rhs expression

        Returns
        -------
        rhs_ex:
            The rhs expression to set
        """
        if not isinstance(rhs_ex, LpExpression):
            raise ValueError('RHS of LpConstraint must be LpExpression')

        self._rhs_expression = rhs_ex  # pylint: disable=W0201

    @property
    def sense(self) -> str:
        """ Getter for the sense of the constraint """
        return self._sense

    @sense.setter
    def sense(self, snse: str) -> None:
        """ Setter for the sense of the constraint. Raises error if not one of 'leq', 'eq', 'geq'

        Parameters
        ----------
        snse:
            The sense to set
        """
        try:
            assert snse.lower() in ('leq', 'eq', 'geq')
            self._sense = snse.lower()  # pylint: disable=W0201
        except (AttributeError, AssertionError):
            raise ValueError("Sense must be one of ('leq', 'eq', 'geq')")

    @property
    def lower_bound(self) -> Optional[Numeric]:
        """ Returns the lower bound on the shifted expression """
        if self.sense == 'leq':
            return None
        return self.rhs_expression.const - self.lhs_expression.const

    @property
    def upper_bound(self) -> Optional[Numeric]:
        """ Returns the upper bound on the shifted expression """
        if self.sense == 'geq':
            return None
        return self.rhs_expression.const - self.lhs_expression.const

    @property
    def slack(self) -> bool:
        """ Getter for slack indicator """
        return self._slack

    @slack.setter
    def slack(self, slck: bool) -> None:
        """ Setter for slack indicator

        Parameters
        ----------
        slck:
            Whether the constraint has slack
        """
        if slck not in (True, False):
            raise ValueError('Slack indicator must be True or False')

        self._slack = slck  # pylint: disable=W0201

    @property
    def slack_variable(self) -> LpVariable:
        """ Getter for the slack variable of the problem. Sets if does not exist. """
        self._slack_variable = (self._slack_variable or LpVariable(name=self.name + '_slack_variable',
                                                                   var_type=VarType.Continuous,
                                                                   low_bound=0)) if self.slack else None
        return self._slack_variable

    @property
    def slack_penalty(self) -> Numeric:
        """ Getter for slack penalty of the constraint """
        return self._slack_penalty

    @slack_penalty.setter
    def slack_penalty(self, penalty: Numeric) -> None:
        """ Setter for slack penalty of the constraint. Raises error if negative.

        Parameters
        ----------
        penalty:
            The slack penalty to set
        """
        if penalty < 0:
            raise ValueError('Slack penalty must be nonnegative')
        if penalty == 0 and self.slack:
            warnings.warn('Slack penalty is zero. No incentive to meet this constraint')

        self._slack_penalty = penalty  # pylint: disable=W0201

    def check(self) -> bool:
        """ Checks if the constraint is satisfied given variable assignments """
        return {'leq': operator.le,
                'eq': operator.eq,
                'geq': operator.ge}[self.sense](self.lhs_expression.evaluate() +
                                                (0 if not self.slack else self.slack_variable.evaluate() *
                                                 (-1 if self.sense == 'leq' else 1)),
                                                self.rhs_expression.evaluate())

    def to_cplex_lp_constraint(self, name: str) -> str:
        """ Returns a constraint as a string

        Parameters
        ----------
        name:
            The name of the constraint
        """
        # Add on the slack only when writing the constraint out
        lhs_result, line = self.lhs_expression.to_cplex_variables_only(name,
                                                                       slack={self.slack_variable: -1 if self.sense == 'leq' else 1}
                                                                       if self.slack else None)
        if self.lhs_expression.const:
            if self.lhs_expression.const < 0:
                term = f" - {-self.lhs_expression.const}"
                line += [term]
            elif self.lhs_expression.const > 0:
                term = f" + {self.lhs_expression.const}"
                line += [term]

        if not list(self.lhs_expression.expr.keys()):
            line += ["0"]
        if self.sense.lower() == 'leq':
            sense = '<='
        elif self.sense.lower() == 'geq':
            sense = '>='
        else:
            sense = '='

        rhs_result, rhs_line = self.rhs_expression.to_cplex_variables_only(name)

        # Could probably do some better checks on line length when trying to do combining
        if not list(self.rhs_expression.expr.keys()) and not self.rhs_expression.const:
            rhs_line += ["0"]

        # Note this does not check the length
        # If variables exist
        if list(self.rhs_expression.expr.keys()):
            if self.rhs_expression.const < 0:
                term = f" - {-self.rhs_expression.const}"
            elif self.rhs_expression.const > 0:
                term = f" + {self.rhs_expression.const}"
            rhs_line += [term]
        else:
            term = str(self.rhs_expression.const)
            rhs_line += [term]

        term = f" {sense} {rhs_result[0][1:] if rhs_result else ''.join(rhs_line[1:]) if rhs_line else ''}"
        if _count_characters(line) + len(term) > LpCplexLPLineSize:
            lhs_result += ["".join(line)]
            line = [term]
        else:
            line += [term]
        lhs_result += ["".join(line)]

        if rhs_result:
            lhs_result += ["".join(rhs_line)]

        result = '\n'.join(lhs_result)
        return f"{result}\n"
