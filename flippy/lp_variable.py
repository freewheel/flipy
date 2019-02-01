class LpVariable:
    def __init__(self, name, var_type='Continuous', up_bound=None, low_bound=None):
        self._name = name
        if var_type not in ['Continuous', 'Integer', 'Binary']:
            raise ValueError('var_type must be one of "Continuous", "Integer", "Binary"')
        self.var_type = var_type
        if up_bound < low_bound:
            raise ValueError('lower bound cannot be above upper bound')
        self.upBound = up_bound
        self.lowBound = low_bound
        self._value = None

    @property
    def name(self):
        return self._name

    def evaluate(self):
        return self._value

    def set_value(self, value):
        self._value = value

    def __hash__(self):
        return id(self)

