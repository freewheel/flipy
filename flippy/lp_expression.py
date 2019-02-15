import math
from collections import defaultdict
from typing import Optional, Mapping, Union, NoReturn

from flippy.lp_variable import LpVariable


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

    def __eq__(self, other):
        return (isinstance(other, LpExpression)
                and self.expr == other.expr
                and self.const == other.const)
