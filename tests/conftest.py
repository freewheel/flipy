import pytest
from flippy import lp_variable


@pytest.fixture
def x():
    return lp_variable.LpVariable('x', low_bound=0, up_bound=10)


