from enum import Enum
from typing import Optional
from flipy.utils import Numeric


class VarType(Enum):
    """ Variable types for LpVariable """
    Continuous = 1
    Integer = 2
    Binary = 3


class LpVariable:
    """ A class representing a linear variable """

    def __init__(self, name: str, var_type: VarType = VarType.Continuous, up_bound: Optional[Numeric] = None,
                 low_bound: Optional[Numeric] = None) -> None:
        """ Initialize the linear variable

        Raises
        ------
        ValueError
            If `var_type` is not one of `VarType.Continuous`, `VarType.Integer`, `VarType.Binary`

        Parameters
        ----------
        name:
            The name of the variable
        var_type:
            The type of variable (continuous, binary, or integer)
        up_bound:
            The upper bound for the variable
        low_bound:
            The lower bound for the variable
        """

        self._name = name

        if var_type not in (VarType.Continuous, VarType.Integer, VarType.Binary):
            raise ValueError(f'var_type must be one of VarType.Continuous, VarType.Integer, VarType.Binary, not {var_type}')
        self._var_type = var_type
        if self._var_type == VarType.Binary:
            self._up_bound = min(up_bound or 1, 1)
            self._low_bound = max(low_bound or 0, 0)
        else:
            self._up_bound = up_bound
            self._low_bound = low_bound
        self._value = None
        self._obj_coeff = None

    @property
    def name(self) -> str:
        """ Getter for name of variable """
        return self._name

    @property
    def var_type(self) -> VarType:
        """ Getter for type of variable """
        return self._var_type

    @var_type.setter
    def var_type(self, v_type: VarType) -> None:
        """ Setter for type of variable

        Raises
        ------
        ValueError
            If `var_type` is not one of `VarType.Continuous`, `VarType.Integer` or `VarType.Binary`

        Parameters
        ----------
        v_type:
            The type to set
        """
        if not isinstance(v_type, VarType):
            raise ValueError('var_type must be one of Continuous, Integer, Binary not %s' % v_type)
        self._var_type = v_type

    def evaluate(self) -> Numeric:
        """ Returns the value of the variable if set """
        if self._value is None:
            raise ValueError('Value of variable %s is None' % self.name)
        return self._value

    def set_obj_coeff(self, coeff: Numeric):
        """ Setter for the objective coefficient of this variable

        Parameters
        ----------
        coeff
            The coefficient of the variable in the objective function
        """
        self._obj_coeff = coeff

    @property
    def obj_coeff(self):
        """ Getter for the coefficient of the variable in the objective function """
        return self._obj_coeff or 0

    def set_value(self, value: Numeric) -> None:
        """ Setter for the value of the variable. Raises errors if not in bounds or if mismatched type.

        Raises
        ------
        ValueError
            If value does not meet variable's bounds or variable type

        Parameters
        ----------
        value:
            The value to set for the variable
        """
        self._value = value

    @property
    def value(self) -> Numeric:
        """ Getter for the value of the variable """
        return self._value

    def __hash__(self) -> int:
        """ Hash function for the LpVariable """
        return id(self)

    @property
    def low_bound(self) -> Optional[Numeric]:
        """ Getter for lower bound of variable """
        return self._low_bound

    @low_bound.setter
    def low_bound(self, bound: Optional[Numeric]) -> None:
        """ Setter for lower bound of variable. Raises error if inconsistent bounds.

        Raises
        ------
        ValueError
            If variable's lower bound is higher than the upper bound

        Parameters
        ----------
        bound:
            The lower bound to set
        """
        if self.up_bound is not None:
            if bound > self.up_bound:
                raise ValueError('lower bound {low} cannot be above upper bound {u}'.format(low=bound, u=self.up_bound))
        self._low_bound = bound

    @property
    def up_bound(self) -> Optional[Numeric]:
        """ Getter for upper bound of variable """
        return self._up_bound

    @up_bound.setter
    def up_bound(self, bound: Optional[Numeric]) -> None:
        """ Setter for upper bound of variable. Raises error if inconsistent bounds.

        Raises
        ------
        ValueError
            If variable's upper bound is lower than the lower bound

        Parameters
        ----------
        bound:
            The upper bound to set
        """
        if self.low_bound is not None:
            if bound < self.low_bound:
                raise ValueError('upper bound {u} cannot be below lower bound {low}'.format(u=bound, low=self.low_bound))
        self._up_bound = bound

    def is_positive_free(self) -> bool:
        """ Tells whether the variable is an unbounded non-negative """
        return self.low_bound == 0 and self.up_bound is None

    def is_free(self) -> bool:
        """ Tells whether the variable is unbounded """
        return self.low_bound is None and self.up_bound is None

    def is_constant(self) -> bool:
        """ Tells whether the variable is restricted to a constant value """
        return self.low_bound is not None and self.up_bound == self.low_bound

    def to_lp_str(self) -> str:
        """ Converts variable into lp format """
        if self.is_free():
            return f'{self.name} free'
        if self.is_constant():
            return f'{self.name} = {self.low_bound:.12g}'

        if self.low_bound is None:
            lhs = '-inf <= '
        elif self.low_bound == 0 and self.var_type == VarType.Continuous:
            lhs = ''
        else:
            lhs = f'{self.low_bound:.12g} <= '

        if self.up_bound is not None:
            rhs = f' <= {self.up_bound:.12g}'
        else:
            rhs = ''
        return lhs + self.name + rhs
