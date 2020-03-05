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

    def test_value(self, x):
        x.set_value(2)
        assert x.evaluate() == 2

    def test_write(self, x):
        assert x.to_lp_str() == 'x <= 10'
