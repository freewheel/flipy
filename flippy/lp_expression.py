from typing import Optional, Mapping, Union, NoReturn

class LpVariable():
    pass

Numeric = Union[int, float]

class LpExpression(object):
    def __init__(self, name: str='', expression: Optional[Mapping[LpVariable, Numeric]] = None, constant: Numeric=0):
        self.name = name
        self.expr = expression
        self.const = constant
