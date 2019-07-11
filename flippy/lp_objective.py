from typing import Optional, Mapping
from flippy.lp_variable import LpVariable
from flippy.lp_expression import LpExpression, Numeric


class Minimize:
    pass


class Maximize:
    pass


class LpObjective(LpExpression):
    def __init__(self, name: str='', expression: Optional[Mapping[LpVariable, Numeric]] = None, constant: Numeric=0,
                 sense=Minimize):
        super(LpObjective, self).__init__(name, expression, constant)
        self._sense = None

        self.sense = sense

    @property
    def sense(self):
        return self._sense

    @sense.setter
    def sense(self, sense):
        if sense not in [Minimize, Maximize]:
            raise ValueError("Sense must be one of %s, %s not %s" % (Minimize, Maximize, sense))
        self._sense = sense
