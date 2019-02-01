from enum import Enum


class VarType(Enum):
    Continuous = 1
    Integer = 2
    Binary = 3


class LpVariable:
    def __init__(self, name, var_type=VarType.Continuous, up_bound=None, low_bound=None):
        self._name = name

        self._var_type = None
        self._up_bound = None
        self._low_bound = None
        self._value = None

        self.var_type = var_type
        self.up_bound = up_bound
        self.low_bound = low_bound

    @property
    def name(self):
        return self._name

    @property
    def var_type(self):
        return self._var_type

    @var_type.setter
    def var_type(self, v_type):
        if not isinstance(v_type, VarType):
            raise ValueError('var_type must be one of Continuous, Integer, Binary not %s' % v_type)
        self._var_type = v_type

    def evaluate(self):
        if self._value is None:
            raise ValueError('Value of variable %s is None' % self.name)
        return self._value

    def set_value(self, value):
        if self.low_bound is not None:
            if self.low_bound > value:
                raise ValueError('value {v} cannot be below lower bound {b}'.format(v=value, b=self.low_bound))
        if self.up_bound is not None:
            if self.up_bound < value:
                raise ValueError('value {v} cannot be above upper bound {b}'.format(v=value, b=self.up_bound))
        if self.var_type is VarType.Integer:
            if int(value) != value:
                raise TypeError('value {v} must match var_type {t}'.format(v=value, t=self.var_type))
        if self.var_type is VarType.Binary:
            if value not in [0, 1]:
                raise TypeError('value {v} must match var_type {t}'.format(v=value, t=self.var_type))
        self._value = value

    def __hash__(self):
        return id(self)

    @property
    def low_bound(self):
        return self._low_bound

    @low_bound.setter
    def low_bound(self, bound):
        if self.up_bound is not None:
            if bound > self.up_bound:
                raise ValueError('lower bound {low} cannot be above upper bound {u}'.format(low=bound, u=self.up_bound))
        self._low_bound = bound

    @property
    def up_bound(self):
        return self._up_bound

    @up_bound.setter
    def up_bound(self, bound):
        if self.low_bound is not None:
            if bound < self.low_bound:
                raise ValueError('upper bound {u} cannot be below lower bound {low}'.format(u=bound, low=self.low_bound))
        self._up_bound = bound
