from enum import Enum


class SolutionStatus(Enum):
    """ Statuses of solutions """
    Optimal = 1
    Infeasible = 2
    Unbounded = 3
    NotSolved = 4
