from flippy.lp_variable import LpVariable
from flippy.lp_constraint import LpConstraint
from flippy.objective import Objective


class LpProblem(object):

    def __init__(self, name, lp_objective=None, lp_constraints=None):
        self.name = name
        self.lp_constraints = dict()
        self.lp_variables = dict()

        self.lp_objective = None
        if lp_objective:
            self.set_objective(lp_objective)

        if lp_constraints:
            for lp_constraint in lp_constraints:
                self.add_constraint(lp_constraint)

    def add_variable(self, lp_variable):
        if not isinstance(lp_variable, LpVariable):
            raise Exception('%s is not an LpVariable' % lp_variable)
        if self.lp_variables.get(lp_variable.name, lp_variable) != lp_variable:
            raise Exception('LP variable name %s conflicts with an existing LP variable' % lp_variable.name)
        self.lp_variables[lp_variable.name] = lp_variable

    def set_objective(self, lp_objective):
        if not isinstance(lp_objective, Objective):
            raise Exception('%s is not an Objective' % lp_objective)
        if self.lp_objective:
            raise Exception('LP objective is already set')
        for var in lp_objective.expr.keys():
            self.add_variable(var)
        self.lp_objective = lp_objective

    def add_constraint(self, lp_constraint):
        if not isinstance(lp_constraint, LpConstraint):
            raise Exception('%s is not an LpConstraint' % lp_constraint)
        if self.lp_constraints.get(lp_constraint.name, lp_constraint) != lp_constraint:
            raise Exception('LP constraint name %s conflicts with an existing LP constraint' % lp_constraint.name)
        self.lp_constraints[lp_constraint.name] = lp_constraint
        for var in lp_constraint.lhs_expression.expr.keys():
            self.add_variable(var)
        for var in lp_constraint.rhs_expression.expr.keys():
            self.add_variable(var)

    def solve(self):
        pass

    def read_lp(self):
        pass

    def write_lp(self):
        pass

