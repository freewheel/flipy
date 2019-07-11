from flippy.lp_variable import LpVariable, VarType
from flippy.lp_constraint import LpConstraint
from flippy.lp_objective import LpObjective, Minimize


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
        if not isinstance(lp_objective, LpObjective):
            raise Exception('%s is not an LpObjective' % lp_objective)
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

    def writeLP(self, buffer, mip = 1):
        """
        Write the given Lp problem to a .lp file.

        This function writes the specifications (objective function,
        constraints, variables) of the defined Lp problem to a file.

        :param buffer:  string buffer

        Side Effects:
            - The file is created.
        """
        if not self.lp_objective:
            raise Exception('No objective')

        buffer.write("\\* "+self.name+" *\\\n")
        if self.lp_objective.sense == Minimize:
            buffer.write("Minimize\n")
        else:
            buffer.write("Maximize\n")

        objName = self.lp_objective.name

        if not objName: objName = "OBJ"
        buffer.write(self.lp_objective.asCplexLpAffineExpression(objName, constant = 0))
        buffer.write("Subject To\n")
        ks = list(self.lp_constraints.keys())
        ks.sort()
        for k in ks:
            constraint = self.lp_constraints[k]
            buffer.write(constraint.asCplexLpConstraint(k))

        vs = self.lp_variables
        # check if any names are longer than 100 characters
        long_names = [v for v in vs if len(v) > 100]
        if long_names:
            raise Exception('Variable names too long for Lp format\n' + str(long_names))

        # Bounds on non-"positive" variables
        # Note: XPRESS and CPLEX do not interpret integer variables without
        # explicit bounds
        if mip:
            vg = [self.lp_variables[v] for v in vs if not self.lp_variables[v].is_positive() and
                  self.lp_variables[v].var_type is VarType.Continuous]
        else:
            vg = [self.lp_variables[v] for v in vs if not self.lp_variables[v].is_positive()]
        if vg:
            buffer.write("Bounds\n")
            for v in vg:
                buffer.write("%s\n" % v.asCplexLpVariable())
        if mip:
            # Integer non-binary variables
            vg = [self.lp_variables[v] for v in vs if self.lp_variables[v].var_type is VarType.Integer]
            if vg:
                buffer.write("Generals\n")
                for v in vg: buffer.write("%s\n" % v.name)
            # Binary variables
            vg = [self.lp_variables[v] for v in vs if self.lp_variables[v].var_type is VarType.Binary]
            if vg:
                buffer.write("Binaries\n")
                for v in vg:
                    buffer.write("%s\n" % v.name)

        buffer.write("End\n")

        return buffer
