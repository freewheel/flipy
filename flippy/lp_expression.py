from collections import defaultdict

from typing import Optional, Mapping, Union, NoReturn

class LpVariable():
    pass

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
        if isinstance(other, LpExpression) and other.expr == self.expr and other.const == self.const:
            return True
        return False

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
