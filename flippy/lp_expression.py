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
        result = [(v.name, v) for v in self.expr.keys()]
        result.sort()
        result = [v for _, v in result]
        return result

    def asCplexVariablesOnly(self, name):
        """
        helper for asCplexLpAffineExpression
        """
        result = []
        line = ["%s:" % name]
        notFirst = 0
        variables = self.sorted_keys()
        for v in variables:
            val = self.expr[v]
            if val < 0:
                sign = " -"
                val = -val
            elif notFirst:
                sign = " +"
            else:
                sign = ""
            notFirst = 1
            if val == 1:
                term = "%s %s" %(sign, v.name)
            elif val == 0:
                continue
            else:
                term = "%s %.12g %s" % (sign, val, v.name)

            if _count_characters(line) + len(term) > LpCplexLPLineSize:
                result += ["".join(line)]
                line = [term]
            else:
                line += [term]
        return result, line

    def asCplexLpAffineExpression(self, name, constant = 1):
        """
        returns a string that represents the Affine Expression in lp format
        """
        #refactored to use a list for speed in iron python
        result, line = self.asCplexVariablesOnly(name)
        if not self.expr or all(self.expr[x] == 0 for x in self.expr):
            term = " %s" % self.const
        else:
            term = ""
            if constant:
                if self.const < 0:
                    term = " - %s" % (-self.const)
                elif self.const > 0:
                    term = " + %s" % self.const
        if _count_characters(line) + len(term) > LpCplexLPLineSize:
            result += ["".join(line)]
            line = [term]
        else:
            line += [term]
        result += ["".join(line)]
        result = "%s\n" % "\n".join(result)
        return result

