import math
from collections import defaultdict
from typing import Optional, Mapping, Union, NoReturn

from flippy.lp_variable import LpVariable
from flippy.utils import LpCplexLPLineSize, _count_characters


Numeric = Union[int, float]


class LpExpression(object):
    def __init__(self, name: str='', expression: Optional[Mapping[LpVariable, Numeric]] = None, constant: Numeric=0):
        self.name = name
        if expression is None:
            self.expr = defaultdict(int)
        else:
            self.expr = defaultdict(int, expression)
        self.const = constant

    def __eq__(self, other):
        if not isinstance(other, LpExpression) or not math.isclose(self.const, other.const):
            return False
        return all(math.isclose(self.expr[var], other.expr[var]) for var in set(self.expr.keys()) | set(other.expr.keys()))

    def evaluate(self):
        return sum(var.evaluate() * coeff for var, coeff in self.expr.items()) + self.const

    def add_expression(self, other):
        for var, coeff in other.expr.items():
            self.expr[var] += coeff
        self.const += other.const

    def add_variable(self, var):
        self.expr[var] += 1

    def add_constant(self, const):
        self.const += const

    def sorted_keys(self):
        """
        returns the list of keys sorted by name
        """
        return sorted((v for v in self.expr.keys()), key=lambda v: v.name)

    def to_cplex_variables_only(self, name, is_first=True, take_inverse=False, slack=None):
        """

        Parameters
        ----------
        slack: dict(LpVariable -> float): all slack variables being used and their coefficients
        """
        result = []
        line = [f"{name}:"]
        variables = self.sorted_keys()
        slack = slack or {}
        variables += list(slack.keys())
        for v in variables:
            # When adding slack the coefficient should be -1 for leq and +1 for geq to make constraint easier to satisfy
            val = slack[v] if v in slack else self.expr[v]
            if val < 0:
                sign = ' -' if not take_inverse else ' +'
                val = -val
            elif is_first:
                sign = ''
            else:
                sign = ' +' if not take_inverse else ' -'
            is_first = False
            if val == 1:
                term = f'{sign} {v.name}'
            elif val == 0:
                continue
            else:
                term = f'{sign} {val:.12g} {v.name}'

            if _count_characters(line) + len(term) > LpCplexLPLineSize:
                result += ["".join(line)]
                line = [term]
            else:
                line += [term]
        return result, line

    def to_cplex_lp_affine_expr(self, name, constant=1, slack=None):
        """
        returns a string that represents the Affine Expression in lp format
        """
        #refactored to use a list for speed in iron python
        result, line = self.to_cplex_variables_only(name, slack=slack)
        if not self.expr or all(self.expr[x] == 0 for x in self.expr):
            term = f" {self.const}"
        else:
            term = ""
            if constant:
                if self.const < 0:
                    term = f" - {-self.const}"
                elif self.const > 0:
                    term = f" + {self.const}"
        if _count_characters(line) + len(term) > LpCplexLPLineSize:
            result += ["".join(line)]
            line = [term]
        else:
            line += [term]
        result += ["".join(line)]
        result = "\n".join(result)
        return f'{result}\n'

