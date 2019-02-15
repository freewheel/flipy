import pytest
from flippy.lp_variable import LpVariable


@pytest.fixture
def x():
    return LpVariable('x', low_bound=0, up_bound=10)


@pytest.fixture
def y():
    return LpVariable('x', low_bound=0, up_bound=5)
