from enum import Enum


class SolutionStatus(Enum):
    Optimal = 1
    Infeasible = 2
    Unbounded = 3
    NotSolved = 4
