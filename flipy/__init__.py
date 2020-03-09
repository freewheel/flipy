"""FreeWheel Linear Programming Interface for Python"""

from flipy.lp_reader import LpReader
from flipy.lp_problem import LpProblem
from flipy.lp_constraint import LpConstraint
from flipy.lp_expression import LpExpression
from flipy.solvers.cbc_solver import CBCSolver
from flipy.lp_variable import LpVariable, VarType
from flipy.solvers.base_solver import SolutionStatus
try:
    from flipy.solvers.gurobi_solver import GurobiSolver
except ImportError:
    class GurobiSolver:
        """ Dumb GurobiSolver class that returns an error when called """
        def __init__(self, *args, **kwargs):
            raise ModuleNotFoundError('gurobipy not installed')
from flipy.lp_objective import LpObjective, Minimize, Maximize

version = '0.0.3'
