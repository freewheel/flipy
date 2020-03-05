import math
from collections import defaultdict
from typing import Optional, Mapping, List

from flipy.lp_variable import LpVariable
from flipy.utils import Numeric


class LpExpression:
    """ A class representing a linear expression """

    def __init__(self, name: str = '', expression: Optional[Mapping[LpVariable, Numeric]] = None,
                 constant: Numeric = 0) -> None:
        """ Initialize the expression

        Parameters
        ----------
        name:
            The name of the expression
        expression:
            Dictionary representing variables and their coefficients
        constant:
            The constant term for the expression
        """
        self.name = name
        if expression is None:
            self.expr = defaultdict(int)
        else:
            self.expr = defaultdict(int, expression)
        self.const = constant

    def __eq__(self, other: 'LpExpression') -> bool:
        """ An equality function for LpExpressions

        Parameters
        ----------
        other:
            The expression to compare against

        Returns
        -------
        bool
            True if the two expression equals to each other
        """
        if not isinstance(other, LpExpression) or not math.isclose(self.const, other.const):
            return False
        return all(math.isclose(self.expr[var], other.expr[var]) for var in set(self.expr.keys()) | set(other.expr.keys()))

    def evaluate(self) -> Numeric:
        """ Gives the value of the expression """
        return sum(var.evaluate() * coeff for var, coeff in self.expr.items()) + self.const

    def add_expression(self, other: 'LpExpression') -> None:
        """ Adds another expression to this expression (summing coefficients)

        Parameters
        ----------
        other:
            The expression to add
        """
        for var, coeff in other.expr.items():
            self.expr[var] += coeff
        self.const += other.const

    def add_variable(self, var: LpVariable) -> None:
        """ Adds a variable to the expression (with coefficient 1)

        Parameters
        ----------
        var:
            The variable to add to the expression
        """
        self.expr[var] += 1

    def add_constant(self, const: Numeric) -> None:
        """ Adds a constant to the expression (adds to existing constant)

        Parameters
        ----------
        const:
            The constant to add
        """
        self.const += const

    def sorted_keys(self) -> List[LpVariable]:
        """ Returns a list of variable in the expression sorted by name """
        return sorted((v for v in self.expr.keys()), key=lambda v: v.name)

    @staticmethod
    def _to_lp_term_str(var_name, coeff, is_first=False):
        """ Converts a variable and coefficient pair into a term string

        >>> LpExpression._to_lp_term_str('x', 5, is_first=True)
        '5 x'
        >>> LpExpression._to_lp_term_str('x', 5)
        '+ 5 x'

        Parameters
        ----------
        var_name: str
            Name of the variable
        coeff: int or float
            Coefficient of the variable
        is_first: bool
            Whether the variable is the first variable in an expression

        Returns
        -------
        str
            The term in string
        """
        if coeff > 0:
            sign = '' if is_first else '+ '
            if coeff == 1:
                return f'{sign}{var_name}'
            return f'{sign}{coeff:.12g} {var_name}'
        if coeff < 0:
            sign = '- '
            if coeff == -1:
                return f'{sign}{var_name}'
            return f'{sign}{-coeff:.12g} {var_name}'
        return ''

    def to_lp_terms(self, slack: Optional[Mapping[LpVariable, Numeric]] = None) -> List[str]:
        """ Returns a list of string that represents the expression in lp format split in terms

        Parameters
        ----------
        slack:
            All slack variables being used and their coefficients

        Returns
        -------
        list(str)
            List of terms in string
        """
        terms = []
        is_first = True
        slack = slack or {}
        for var in self.sorted_keys():
            coeff = self.expr[var]
            terms.append(self._to_lp_term_str(var.name, coeff, is_first=is_first))
            is_first = False

        for slack_var in sorted(slack.keys(), key=lambda v: v.name):
            coeff = slack[slack_var]
            terms.append(self._to_lp_term_str(slack_var.name, coeff, is_first=is_first))
            is_first = False

        if self.const < 0:
            terms.append(f'- {-self.const}')
        elif self.const > 0:
            terms.append(f'+ {self.const}')
        elif self.const == 0 and not terms:
            terms.append(f'{self.const}')
        return terms
