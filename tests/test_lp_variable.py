import pytest
from flipy.lp_variable import LpVariable, VarType


@pytest.mark.usefixtures('x')
class TestLpVariable(object):
    def test_bound_error(self):
        z = LpVariable('z')
        z.low_bound = 2
        with pytest.raises(ValueError) as e:
            z.up_bound = 1
        assert 'cannot be below lower bound' in str(e.value)
        z.up_bound = 4
        with pytest.raises(ValueError) as e:
            z.low_bound = 5
        assert 'cannot be above upper bound' in str(e.value)
        z.low_bound = 1
        assert z.low_bound == 1
        assert z.up_bound == 4

    def test_types(self):
        with pytest.raises(ValueError) as e:
            LpVariable('z', var_type='None')
        assert 'var_type must be one of VarType.Continuous, VarType.Integer, VarType.Binary, not None' in str(e.value)
        z = LpVariable('z', var_type=VarType.Integer)
        with pytest.raises(ValueError) as e:
            z.set_value(3.5)
        assert 'must match var_type' in str(e.value)
        z.set_value(3)
        z = LpVariable('z', var_type=VarType.Binary)
        with pytest.raises(ValueError) as e:
            z.set_value(0.5)
        assert 'must match var_type' in str(e.value)
        z.set_value(0)
        z.set_value(1)

    def test_value(self, x):
        with pytest.raises(ValueError) as e:
            x.evaluate()
        assert 'is None' in str(e.value)
        x.set_value(2)
        assert x.evaluate() == 2
        with pytest.raises(ValueError) as e:
            x.set_value(12)
        assert 'cannot be' in str(e.value)

    def test_write(self, x):
        assert x.to_lp_str() == 'x <= 10'
