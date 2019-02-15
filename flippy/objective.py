from typing import Optional, Mapping
from flippy.lp_variable import LpVariable
from flippy.lp_expression import LpExpression, Numeric


class Minimize:
    pass


class Maximize:
    pass


class Objective(LpExpression):
    def __init__(self, name: str='', expression: Optional[Mapping[LpVariable, Numeric]] = None, constant: Numeric=0,
                 sense=Minimize):
        super(Objective, self).__init__(name, expression, constant)
        self._sense = None

        self.sense = sense

    @property
    def sense(self):
        return self._sense

    @sense.setter
    def sense(self, sense):
        if sense not in [Minimize, Maximize]:
            raise ValueError("Sense must be one of <class 'flippy.objective.Minimize'>, "
                             "<class 'flippy.objective.Maximize'> not %s" % sense)
        self._sense = sense
