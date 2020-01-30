import pytest
import math
from flipy.lp_expression import LpExpression
from collections import defaultdict
from flipy.lp_expression import LpExpression
from flipy.lp_variable import LpVariable

@pytest.fixture
def expression(x):
   return LpExpression(name='test_expr', expression={x: 998}, constant=8)

@pytest.fixture
def z():
    return LpVariable(name='z')

@pytest.fixture
def expression_2(x, y, z):
    return LpExpression(name='text_expr_2', expression={x:-5, y:-2, z:0}, constant=0)
    

@pytest.mark.usefixtures('expression', 'expression_2', 'x', 'y', 'z')
class TestLpExpression(object):
    def test_init(self):
        expression = LpExpression('', None, 5)
        assert expression.name == ''
        assert type(expression.expr) == defaultdict
        assert expression.const == 5

    def test_evaluate(self, expression, x):
        x.set_value(5)
        assert expression.evaluate() == 4998

    def test_add_expression(self, expression, expression_2, x, y, z):
        expression.add_expression(expression_2)
        assert len(expression.expr) == 3
        assert expression.const == 8
        assert expression.expr[x] == 993
        assert expression.expr[y] == -2
        assert expression.expr[z] == 0

    def test_add_variable(self, expression, x, y):
        expression.add_variable(x)
        assert expression.expr[x] == 999
        expression.add_variable(y)
        assert expression.expr[y] == 1

    def test_add_constant(self, expression):
        expression.add_constant(0)
        assert expression.const == 8
        expression.add_constant(-8.2)
        assert math.isclose(expression.const, -0.2)

    def test__eq__(self, expression, x, y):
        assert expression == LpExpression(name='text_expr_3', expression={x: 998, y: 0}, constant=8.0)

    def test_to_lp_lp_expr(self, x, y):
        expr = LpExpression(expression={x: 1, y: -1}, constant=100)
        assert expr.to_lp_terms() == ['x', '- y', '+ 100']

    def test_to_lp_lp_expr_constant_zero(self, expression):
        expr = LpExpression(expression={}, constant=0)
        assert expr.to_lp_terms() == ['0']
