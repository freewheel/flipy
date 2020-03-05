import copy
import operator
import warnings
from typing import Optional, List

from flipy.lp_expression import LpExpression
from flipy.lp_variable import LpVariable, VarType
from flipy.utils import Numeric


class LpConstraint:
    """ A class representing a linear constraint """

    def __init__(self, lhs: LpExpression, sense: str, rhs: Optional[LpExpression] = None, name:
                 Optional[str] = None, slack: bool = False, slack_penalty: Numeric = 0, copy_expr: bool = False) -> None:
        """ Initialize the constraint

        Parameters
        ----------
        lhs:
            The left-hand-side expression
        sense:
            The type of constraint (leq, geq, or eq)
        rhs:
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
        self.lhs = lhs if not copy_expr else copy.copy(lhs)
        if rhs:
            self.rhs = rhs
        else:
            self.rhs = LpExpression()
        self.sense = sense
        self.name = name or ''
        self.slack = slack
        self.slack_penalty = slack_penalty

        self._slack_variable = None

    def _shift_variables(self):
        """ Shifts all variables to the left hand side of the constraint, and shifts the
        constant to the right hand side of the constraints

        Returns
        -------
        flipy.LpExpression
            The shfited lhs expression
        float
            The shifted rhs constant
        """
        new_expr = LpExpression(expression=copy.copy(self.lhs.expr))

        for var, coeff in self.rhs.expr.items():
            new_expr.expr[var] -= coeff

        if self.slack:
            new_expr.expr[self.slack_variable] = -1 if self.sense == 'leq' else 1

        const = self.rhs.const - self.lhs.const
        return new_expr, const

    def _shift_constant_right(self) -> None:
        """ Moves the constant on the lhs to the rhs """
        if not self.lhs.const:
            return
        self.rhs.const -= self.lhs.const
        self.lhs.const = 0

    @property
    def lhs(self) -> LpExpression:
        """ Getter for lhs expression """
        return self._lhs

    @lhs.setter
    def lhs(self, lhs_exp: LpExpression) -> None:
        """ Setter for lhs expression

        Raises
        ------
        ValueError
            If `lhs_exp` is not an LpExpression objective

        Parameters
        ----------
        lhs_exp:
            The lhs expression to set
        """
        if not isinstance(lhs_exp, LpExpression):
            raise ValueError('LHS of LpConstraint must be LpExpression')

        self._lhs = lhs_exp  # pylint: disable=W0201

    @property
    def rhs(self) -> LpExpression:
        """ Getter for rhs expression """
        return self._rhs

    @rhs.setter
    def rhs(self, rhs_exp: LpExpression) -> None:
        """ Setter for rhs expression

        Raises
        ------
        ValueError
            If `rhs_exp` is not an LpExpression objective

        Parameters
        -------
        rhs_exp:
            The rhs expression to set
        """
        if not isinstance(rhs_exp, LpExpression):
            raise ValueError('RHS of LpConstraint must be LpExpression')

        self._rhs = rhs_exp  # pylint: disable=W0201

    @property
    def sense(self) -> str:
        """ Getter for the sense of the constraint """
        return self._sense

    @sense.setter
    def sense(self, snse: str) -> None:
        """ Setter for the sense of the constraint. Raises error if not one of 'leq', 'eq', 'geq'

        Raises
        ------
        ValueError
            If `snse` is not one of `leq`, `eq` or `geq`

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
        return self.rhs.const - self.lhs.const

    @property
    def upper_bound(self) -> Optional[Numeric]:
        """ Returns the upper bound on the shifted expression """
        if self.sense == 'geq':
            return None
        return self.rhs.const - self.lhs.const

    def breakdown(self) -> List['LpConstraint']:
        """ Breaks down a equality constraint into an upper bound and a lower bound constraint """
        if self.sense != 'eq':
            return [self]

        upper_bound_constraint = LpConstraint(
            name=self.name + '_ub',
            lhs=LpExpression(expression=copy.copy(self.lhs.expr)),
            rhs=LpExpression(expression=copy.copy(self.rhs.expr)),
            sense='leq',
            slack=self.slack,
            slack_penalty=self.slack_penalty,
        )

        lower_bound_constraint = self
        lower_bound_constraint.sense = 'geq'
        lower_bound_constraint.name += '_lb'
        return [lower_bound_constraint, upper_bound_constraint]

    @property
    def slack(self) -> bool:
        """ Getter for slack indicator """
        return self._slack

    @slack.setter
    def slack(self, slck: bool) -> None:
        """ Setter for slack indicator

        Raises
        ------
        ValueError
            If `slck` is not a bool type variable

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

        Raises
        ------
        ValueError
            If `penalty` has positive value

        Parameters
        ----------
        penalty:
            The slack penalty to set

        Raises
        ------
        ValueError
        """
        if penalty < 0:
            raise ValueError('Slack penalty must be non-negative')
        if penalty == 0 and self.slack:
            warnings.warn('Slack penalty is zero. No incentive to meet this constraint')

        self._slack_penalty = penalty  # pylint: disable=W0201

    def check(self) -> bool:
        """ Checks if the constraint is satisfied given variable assignments """
        return {'leq': operator.le,
                'eq': operator.eq,
                'geq': operator.ge}[self.sense](self.lhs.evaluate() +
                                                (0 if not self.slack else self.slack_variable.evaluate() *
                                                 (-1 if self.sense == 'leq' else 1)),
                                                self.rhs.evaluate())

    def to_lp_terms(self):
        """
        Returns the constraint as a list of terms like ['5', 'a', '<=', '10']

        Returns
        -------
        list(str)
            List of terms in string
        """
        new_expr, const = self._shift_variables()

        if self.sense.lower() == 'leq':
            sense = '<='
        elif self.sense.lower() == 'geq':
            sense = '>='
        else:
            sense = '='

        terms = []
        terms += new_expr.to_lp_terms()
        terms.append(sense)
        terms.append(str(const))
        return terms
