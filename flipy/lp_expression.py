from __future__ import annotations

import math
from collections import defaultdict
from typing import Optional, Mapping, List, Tuple

from flipy.lp_variable import LpVariable
from flipy.utils import LpCplexLPLineSize, _count_characters, Numeric


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

    def __eq__(self, other: LpExpression) -> bool:
        """ An equality function for LpExpressions

        Parameters
        ----------
        other:
            The expression to compare against

        Returns
        -------
        bool
        """
        if not isinstance(other, LpExpression) or not math.isclose(self.const, other.const):
            return False
        return all(math.isclose(self.expr[var], other.expr[var]) for var in set(self.expr.keys()) | set(other.expr.keys()))

    def evaluate(self) -> Numeric:
        """ Gives the value of the expression """
        return sum(var.evaluate() * coeff for var, coeff in self.expr.items()) + self.const

    def add_expression(self, other: LpExpression) -> None:
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

    def to_cplex_variables_only(self, name: str, is_first: bool = True, take_inverse: bool = False,
                                slack: Optional[Mapping[LpVariable, Numeric]] = None) -> Tuple[List[str], List[str]]:
        """ Converts the variables of the expression to cplex format (i.e. ignores constant)

        Parameters
        ----------
        name:
            The name of the expression
        is_first:
            Whether this is the first variable in the expression (probably doesn't need to be a parameter)
        take_inverse:
            Whether to invert the signs of all coefficients
        slack:
            All slack variables being used and their coefficients

        Returns
        -------
        result:
            The list of lines in the LP problem
        line:
            The last line of the LP problem
        """
        result = []
        line = [f"{name}:"]
        variables = self.sorted_keys()
        slack = slack or {}
        variables += list(slack.keys())
        for var in variables:
            # When adding slack the coefficient should be -1 for leq and +1 for geq to make constraint easier to satisfy
            val = slack[var] if var in slack else self.expr[var]
            if val < 0:
                sign = ' -' if not take_inverse else ' +'
                val = -val
            elif is_first:
                sign = ''
            else:
                sign = ' +' if not take_inverse else ' -'
            is_first = False
            if val == 1:
                term = f'{sign} {var.name}'
            elif val == 0:
                continue
            else:
                term = f'{sign} {val:.12g} {var.name}'

            if _count_characters(line) + len(term) > LpCplexLPLineSize:
                result += ["".join(line)]
                line = [term]
            else:
                line += [term]
        return result, line

    def _to_cplex_term_str(self, var_name, coeff, is_first=False):
        if coeff == 0:
            return ''
        if coeff > 0:
            sign = '' if is_first else '+ '
            if coeff == 1:
                return f'{sign}{var_name}'
            else:
                return f'{sign}{coeff:.12g} {var_name}'
        else:
            sign = '- '
            if coeff == -1:
                return f'{sign}{var_name}'
            else:
                return f'{sign}{-coeff:.12g} {var_name}'

    def to_cplex_terms(self, slack: Optional[Mapping[LpVariable, Numeric]] = None) -> List[str]:
        """ Returns a list of string that represents the expression in lp format split in terms

        Parameters
        ----------
        slack:
            All slack variables being used and their coefficients

        Returns
        -------
        list(str)
        """
        terms = []
        is_first = True
        slack = slack or {}
        for var in self.sorted_keys():
            coeff = self.expr[var]
            if coeff == 0:
                continue
            terms.append(self._to_cplex_term_str(var.name, coeff, is_first=is_first))
            is_first = False

        for slack_var in sorted(slack.keys(), key=lambda v: v.name):
            coeff = slack[slack_var]
            if coeff == 0:
                continue
            terms.append(self._to_cplex_term_str(slack_var.name, coeff, is_first=is_first))
            is_first = False

        if self.const < 0:
            terms.append(f'- {-self.const}')
        elif self.const > 0:
            terms.append(f'+ {self.const}')
        elif self.const == 0 and not terms:
            terms.append(f'{self.const}')
        return terms
