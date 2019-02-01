import pytest

@pytest.fixture
def expression(name='', expression=None, constant=0):
    from flippy.lp_expression import LpExpression
    return LpExpression(name, expression, constant)

@pytest.mark.usefixtures('expression')
class TestLpExpression(object):
    def test_init(expression):
        assert expression
    
