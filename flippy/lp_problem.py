import gzip
from flippy.lp_variable import LpVariable, VarType
from flippy.lp_constraint import LpConstraint
from flippy.lp_objective import LpObjective, Minimize, Maximize
from flippy.lp_expression import LpExpression


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

def mathify_expression(string_split):
    # returns dictionary {variables: coefficient}
    dct = {}
    recent_term = {'variable': None, 'coefficient': '1', 'sign': '+'}
    # helper function for adding terms to the dictionary
    def add_recent_term(dct={}, recent_term={'variable': None, 'coefficient': '1', 'sign': '+'}):
        if recent_term['variable']:
            dct[recent_term['variable']] = float(recent_term['sign'] + recent_term['coefficient'])
        pass
    for expr in string_split:
        if expr in {'+', '-'}: # this is the start of a new term
            add_recent_term(dct, recent_term)
            recent_term = {'variable': None, 'coefficient': '1', 'sign': expr}
        try:
            recent_term['coefficient'] = str(float(expr))
        except:
            recent_term['variable'] = expr
    add_recent_term(dct, recent_term)
    return dct


def read_lp(lp_file):
    """ Takes in a filepath to a text file of an LP (written by PuLP or Flippy) and Returns a Flippy LpProblem
    """
    if lp_file[-3:] == '.gz':
            with gzip.open(lp_file, mode='rt') as f:
                content = f.readlines()
    else:
        with open(lp_file) as f:
            content = f.readlines()
    content = [x.strip() for x in content]
    # check there's an 'End' at the end...
    if content[-1] != 'End':
        return "No 'End' at the end, might not be the right kind of file!"
    # get the name of the problem file
    try:
        problem_name = content[0].split(" ")[1]
    except e:
        return "No title, might not be the right kind of file!"
    # get the sense: max/min
    try:
        problem_sense = Maximize if content[1] == 'Maximize' else Minimize
    except ValueError:
        return "Sense as max/min not found, might not be the right kind of file!"

    def lst_find(lst, term):
        try:
            return lst.index(term)
        except:
            return None

    # grab the objective, name: to "subject to"
    try:
        obj_start = 2
        obj_end = content.index('Subject To')
    except ValueError:
        return "Objective, might not be the right kind of file!"

    # these may not be there but grab if they are
    bounds_start = lst_find(content, 'Bounds')
    generals_start = lst_find(content, 'Generals')
    binaries_start = lst_find(content, 'Binaries')

    # if there are contraints:
    constraints_string_split = ' '.join(content[obj_end+1:bounds_start]).strip().split(' ')
    constraint_list = []
    # find all the comparisons
    def find_breaks(split_string):
        return [-2] + [i for i in range(len(split_string)) if split_string[i] in {"<=", '<', '=', '>', ">="}]
    breaks = find_breaks(constraints_string_split)
    # iterate through each constraint and capture
    current_constraint = {'name': None, 'lhs': None, 'sense': None, 'rhs': None}
    for i in range(len(breaks[:-1])):
        raw_lhs_string = ' '.join(constraints_string_split[breaks[i]+2:breaks[i+1]]).strip()
        rhs_string = constraints_string_split[breaks[i+1]+1].strip()
        name = raw_lhs_string.split(':')[0].strip()
        lhs_string = raw_lhs_string.split(':')[1].strip()
        sense = constraints_string_split[breaks[i+1]].strip()
        current_constraint = {'name': name,
                              'lhs': mathify_expression(lhs_string.split(' ')),
                              'sense': sense,
                              'rhs': float(rhs_string)}
        constraint_list.append(current_constraint)

    # if there are Bounds:
    bounds_list = []
    if bounds_start:
        raw_bounds = content[bounds_start+1:(generals_start or binaries_start or -1)]
        # since bounds are just "variable sense value"
        for raw_bound in raw_bounds:
            split_bound = raw_bound.split(' ')
            if len(split_bound) == 3:
                try:
                    float(split_bound[0])
                    #it's the number first, it's 5 <= x
                    bounds_list.append({'variable':split_bound[2],
                                'low_bound': float(split_bound[0]),
                                'up_bound': None})
                except:
                    #it's the variable first
                    if split_bound[1] == '=': # it's x = 5
                        bounds_list.append({'variable': split_bound[0],
                                'low_bound': float(split_bound[2]),
                                'up_bound': float(split_bound[2])})
                    else: # it's x <= 5
                        bounds_list.append({'variable': split_bound[0],
                            'low_bound': None,
                            'up_bound': float(split_bound[2])})
            else: #length is 5 so it's 5 <= x <= 7
                bounds_list.append({'variable':split_bound[2],
                            'low_bound': float(split_bound[0]),
                            'up_bound': float(split_bound[4])})
    # if there are Generals:
    generals_list = []
    if generals_start:
        generals_string = ' '.join(content[generals_start+1:(binaries_start or -1)]).strip()
        generals_list = generals_string.split(' ')
    # if there are Binaries:
    binaries_list = []
    if binaries_start:
        binaries_string = ' '.join(content[binaries_start+1:-1]).strip()
        binaries_list = binaries_string.split(' ')

    obj_string = ' '.join(content[obj_start:obj_end]).strip()
    obj_name = obj_string.split(' ')[0][:-1]
    obj = mathify_expression(obj_string.split(' ')[1:])

    variable_names = set(obj.keys()).union(*[constraint['lhs'].keys() for constraint in constraint_list])
    def get_var_type(string):
        if string in binaries_list:
            return VarType.Binary
        elif string in generals_list:
            return VarType.Integer
        else:
            return VarType.Continuous

    def get_var_up_bound(string):
        if bounds_list:
            if string in set(bound['variable'] for bound in bounds_list):
                return [bound['up_bound'] for bound in bounds_list if bound['variable'] == string][0]
        return None

    def get_var_low_bound(string):
        if bounds_list:
            if string in set(bound['variable'] for bound in bounds_list):
                return [bound['low_bound'] for bound in bounds_list if bound['variable'] == string][0]
        return None

    dictionary_of_variables = {name: LpVariable(name, var_type=get_var_type(name), up_bound=get_var_up_bound(name), low_bound=get_var_low_bound(name)) for name in variable_names}
    objective = LpObjective(name=obj_name, expression={dictionary_of_variables[name]: obj[name] for name in obj}, sense=problem_sense)
    constraints = []
    for constraint in constraint_list:
        rhs_expression = LpExpression(constant=constraint['rhs'])
        lhs_expression = LpExpression(expression={dictionary_of_variables[name]: constraint['lhs'][name] for name in constraint['lhs'].keys()})
        sense = {'<=': 'leq', '>=': 'geq', '=': 'eq'}[constraint['sense']]
        name = constraint['name']
        constraints.append(LpConstraint(lhs_expression, sense, rhs_expression, name))

    return LpProblem(problem_name, objective, constraints)
