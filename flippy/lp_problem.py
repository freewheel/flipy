class LpProblem(object):

    def __init__(self, name, lp_constraint, lp_objective):
        self.name = name
        self.lp_constraint = lp_constraint
        self.lp_objective = lp_objective

    def solve(self):
        pass

    def read_lp(self):
        pass

    def write_lp(self):
        pass

