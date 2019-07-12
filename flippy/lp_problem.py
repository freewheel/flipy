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

    def to_str(self, mip=True):
        result = []
        if not self.lp_objective:
            raise Exception('No objective')
        result.append(f'\\* {self.name} *\\')
        if self.lp_objective.sense == Minimize:
            result.append('Minimize')
        else:
            result.append('Maximize')

        obj_name = self.lp_objective.name if self.lp_objective.name else 'OBJ'

        result.append(self.lp_objective.to_cplex_lp_affine_expr(obj_name, constant=0))
        result.append('Subject To')
        constr_keys = sorted(list(self.lp_constraints.keys()))
        for constr_key in constr_keys:
            constraint = self.lp_constraints[constr_key]
            result.append(constraint.to_cplex_lp_constraint(constr_key))

        variables = self.lp_variables

        if mip:
            vg = [self.lp_variables[v] for v in variables if not self.lp_variables[v].is_positive() and
                  self.lp_variables[v].var_type is VarType.Continuous]
        else:
            vg = [self.lp_variables[v] for v in variables if not self.lp_variables[v].is_positive()]
        if vg:
            result.append('Bounds')
            for v in vg:
                result.append(f'{v.to_cplex_lp_variable()}')
        if mip:
            # Integer non-binary variables
            vg = [self.lp_variables[v] for v in variables if self.lp_variables[v].var_type is VarType.Integer]
            if vg:
                result.append('Generals')
                for v in vg:
                    result.append(v.name)
            # Binary variables
            vg = [self.lp_variables[v] for v in variables if self.lp_variables[v].var_type is VarType.Binary]
            if vg:
                result.append('Binaries')
                for v in vg:
                    result.append(v.name)

        result.append("End")
        return '\n'.join(result)

    def write_lp(self, buffer, mip=1):
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

        buffer.write(f"\\* {self.name} *\\\n")
        if self.lp_objective.sense == Minimize:
            buffer.write("Minimize\n")
        else:
            buffer.write("Maximize\n")

        objName = self.lp_objective.name

        if not objName: objName = "OBJ"
        buffer.write(self.lp_objective.to_cplex_lp_affine_expr(objName, constant=0))
        buffer.write("Subject To\n")
        ks = list(self.lp_constraints.keys())
        ks.sort()
        for k in ks:
            constraint = self.lp_constraints[k]
            buffer.write(constraint.to_cplex_lp_constraint(k))

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
                buffer.write(f"{v.to_cplex_lp_variable()}\n")
        if mip:
            # Integer non-binary variables
            vg = [self.lp_variables[v] for v in vs if self.lp_variables[v].var_type is VarType.Integer]
            if vg:
                buffer.write("Generals\n")
                for v in vg: buffer.write(f"{v.name}\n")
            # Binary variables
            vg = [self.lp_variables[v] for v in vs if self.lp_variables[v].var_type is VarType.Binary]
            if vg:
                buffer.write("Binaries\n")
                for v in vg:
                    buffer.write(f"{v.name}\n")

        buffer.write("End\n")

        return buffer
