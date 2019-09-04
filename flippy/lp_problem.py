import gzip
from typing import Optional, List, TextIO, Mapping, Union

from flippy.lp_variable import LpVariable, VarType
from flippy.lp_constraint import LpConstraint
from flippy.lp_objective import LpObjective, Minimize, Maximize
from flippy.lp_expression import LpExpression
from flippy.utils import Numeric


class LpProblem:
    """ A class representing a linear programming problem """

    def __init__(self, name: str, lp_objective: Optional[LpObjective] = None,
                 lp_constraints: Optional[List[LpConstraint]] = None) -> None:
        """ Initialize the LP problem

        Parameters
        ----------
        name:
            The name of the LP problem
        lp_objective:
            The objective of the LP problem
        lp_constraints:
            The constraints of the LP problem
        """
        self.name = name
        self.lp_constraints = dict()
        self.lp_variables = dict()
        self.slack = dict()

        self.lp_objective = None

        if lp_objective:
            self.set_objective(lp_objective)

        if lp_constraints:
            for lp_constraint in lp_constraints:
                self.add_constraint(lp_constraint)

    def add_variable(self, lp_variable: LpVariable) -> None:
        """ Adds a variable to the internal dictionary of the problem

        Parameters
        ----------
        lp_variable:
            The variable to add
        """
        if not isinstance(lp_variable, LpVariable):
            raise Exception('%s is not an LpVariable' % lp_variable)
        if self.lp_variables.get(lp_variable.name, lp_variable) != lp_variable:
            raise Exception('LP variable name %s conflicts with an existing LP variable' % lp_variable.name)
        self.lp_variables[lp_variable.name] = lp_variable

    def set_objective(self, lp_objective: LpObjective) -> None:
        """ Sets the objective of the LP problem and adds all variables. Raises error if already has an objective.

        Parameters
        ----------
        lp_objective:
            The objective to set
        """
        if not isinstance(lp_objective, LpObjective):
            raise Exception('%s is not an LpObjective' % lp_objective)
        if self.lp_objective:
            raise Exception('LP objective is already set')
        for var in lp_objective.expr.keys():
            self.add_variable(var)
        self.lp_objective = lp_objective

    def add_constraint(self, lp_constraint: LpConstraint) -> None:
        """ Adds a constraint to the LP problem and adds all variables. Raises error if namespace conflict.

        Parameters
        ----------
        lp_constraint:
            The constraint to add
        """
        if not isinstance(lp_constraint, LpConstraint):
            raise Exception('%s is not an LpConstraint' % lp_constraint)
        if self.lp_constraints.get(lp_constraint.name, lp_constraint) != lp_constraint:
            raise Exception('LP constraint name %s conflicts with an existing LP constraint' % lp_constraint.name)
        self.lp_constraints[lp_constraint.name] = lp_constraint
        for var in lp_constraint.lhs_expression.expr.keys():
            self.add_variable(var)
        for var in lp_constraint.rhs_expression.expr.keys():
            self.add_variable(var)

    def solve(self) -> None:
        """ Solve the LP problem """

    def to_str(self, mip: bool = True) -> str:
        """ Convert the LP problem to a str

        Parameters
        ----------
        mip:
            Whether there are integer or binary variables

        """
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
            bounded_vars = [self.lp_variables[var] for var in variables if not self.lp_variables[var].is_positive() and
                            self.lp_variables[var].var_type is VarType.Continuous]
        else:
            bounded_vars = [self.lp_variables[var] for var in variables if not self.lp_variables[var].is_positive()]
        if bounded_vars:
            result.append('Bounds')
            for var in bounded_vars:
                result.append(f'{var.to_cplex_lp_variable()}')
        if mip:
            # Integer non-binary variables
            bounded_vars = [self.lp_variables[var] for var in variables if self.lp_variables[var].var_type is VarType.Integer]
            if bounded_vars:
                result.append('Generals')
                for var in bounded_vars:
                    result.append(var.name)
            # Binary variables
            bounded_vars = [self.lp_variables[var] for var in variables if self.lp_variables[var].var_type is VarType.Binary]
            if bounded_vars:
                result.append('Binaries')
                for var in bounded_vars:
                    result.append(var.name)

        result.append("End")
        return '\n'.join(result)

    def write_lp(self, buffer: TextIO, mip: int = 1) -> TextIO:
        """ Write the given Lp problem to a .lp file.

        This function writes the specifications (objective function,
        constraints, variables) of the defined Lp problem to a file.

        Parameters
        ----------
        buffer:
            Buffer to write the lp to
        mip:
            Whether the lp has integer or binary variables

        Returns
        -------
        buffer
            The buffer with the lp written to it
        """
        if not self.lp_objective:
            raise Exception('No objective')

        buffer.write(f"\\* {self.name} *\\\n")
        if self.lp_objective.sense == Minimize:
            buffer.write("Minimize\n")
        else:
            buffer.write("Maximize\n")

        obj_name = self.lp_objective.name

        if not obj_name:
            obj_name = "OBJ"
        slack = {constraint.slack_variable: constraint.slack_penalty * (1 if self.lp_objective.sense == Minimize else -1)
                 for constraint in self.lp_constraints.values() if constraint.slack}
        buffer.write(self.lp_objective.to_cplex_lp_affine_expr(obj_name, constant=0,
                                                               slack=slack or None))
        buffer.write("Subject To\n")
        keys = list(self.lp_constraints.keys())
        keys.sort()
        for key in keys:
            constraint = self.lp_constraints[key]
            buffer.write(constraint.to_cplex_lp_constraint(key))

        variables = self.lp_variables
        # check if any names are longer than 100 characters
        long_names = [var for var in variables if len(var) > 100]
        if long_names:
            raise Exception('Variable names too long for Lp format\n' + str(long_names))

        # Bounds on non-"positive" variables
        # Note: XPRESS and CPLEX do not interpret integer variables without
        # explicit bounds
        if mip:
            bounded_vars = [self.lp_variables[var] for var in variables if not self.lp_variables[var].is_positive() and
                            self.lp_variables[var].var_type is VarType.Continuous]
        else:
            bounded_vars = [self.lp_variables[var] for var in variables if not self.lp_variables[var].is_positive()]
        if bounded_vars:
            buffer.write("Bounds\n")
            for var in bounded_vars:
                buffer.write(f"{var.to_cplex_lp_variable()}\n")
        if mip:
            # Integer non-binary variables
            bounded_vars = [self.lp_variables[var] for var in variables if self.lp_variables[var].var_type is VarType.Integer]
            if bounded_vars:
                buffer.write("Generals\n")
                for var in bounded_vars:
                    buffer.write(f"{var.name}\n")
            # Binary variables
            bounded_vars = [self.lp_variables[var] for var in variables if self.lp_variables[var].var_type is VarType.Binary]
            if bounded_vars:
                buffer.write("Binaries\n")
                for var in bounded_vars:
                    buffer.write(f"{var.name}\n")

        buffer.write("End\n")

        return buffer


def mathify_expression(string_split: List[str]) -> Mapping[str, str]:
    """ Creates a mapping of variable to coefficient

    Parameters
    ----------
    string_split:
        An expression read from an LP file and split
    """
    # returns dictionary {variables: coefficient}
    dct = {}
    recent_term = {'variable': None, 'coefficient': '1', 'sign': '+'}

    def add_recent_term(dct: Optional[Mapping[str, ]] = None, recent_term: Optional[Mapping[str, ]] = None) -> None:
        """ Helper function for adding terms to the dictionary

        Parameters
        ----------
        dct:
            The dictionary to add the term to
        recent_term:
            A dict representation of the term to add to the dictionary"""
        if dct is None:
            dct = {}
        if recent_term is None:
            recent_term = {'variable': None, 'coefficient': '1', 'sign': '+'}
        if recent_term['variable']:
            dct[recent_term['variable']] = float(recent_term['sign'] + recent_term['coefficient'])

    for expr in string_split:
        if expr in {'+', '-'}: # this is the start of a new term
            add_recent_term(dct, recent_term)
            recent_term = {'variable': None, 'coefficient': '1', 'sign': expr}
        try:
            recent_term['coefficient'] = str(float(expr))
        except ValueError:
            recent_term['variable'] = expr
    add_recent_term(dct, recent_term)
    return dct


# pylint: disable=W0201
class LpReader:
    """ A class for reading lp files """

    def extract_content(self, lp_file: str) -> None:
        """ Reads the contents of the lp_file into a list

        Parameters
        ----------
        lp_file:
            filepath for the LP file to read
        """
        if lp_file[-3:] == '.gz':
            with gzip.open(lp_file, mode='rt') as f:
                self.content = f.readlines()
        else:
            with open(lp_file) as f:
                self.content = f.readlines()
        self.content = [x.strip() for x in self.content]
        # check there's an 'End' at the end...
        if self.content[-1] != 'End':
            raise AttributeError("No 'End' at the end, might not be the right kind of file!")

    def verify(self) -> None:
        """ Verifies the structure of the lp file and sets some member variables """
        # get the name of the problem file
        try:
            self.problem_name = self.content[0].split(" ")[1]
        except IndexError:
            raise AttributeError("No title, might not be the right kind of file!")
        # get the sense: max/min
        try:
            self.problem_sense = Maximize if self.content[1] == 'Maximize' else Minimize
        except ValueError:
            raise AttributeError("Sense as max/min not found, might not be the right kind of file!")

        # grab the objective, name: to "subject to"
        try:
            self.obj_start = 2
            self.obj_end = self.content.index('Subject To')
        except ValueError:
            raise AttributeError("Objective, might not be the right kind of file!")

    @staticmethod
    def lst_find(lst: List, term) -> Optional[int]:
        """ Get the index of a term in a list

        Parameters
        ----------
        lst:
            The list to search through
        term:
            The term to search for
        """
        try:
            return lst.index(term)
        except ValueError:
            return None

    @staticmethod
    # find all the comparisons
    def find_breaks(split_string: List[str]) -> List[int]:
        """ Gets the indices of the equality/inequality symbols in a list of strings

        Parameters
        ----------
        split_string:
            The expression to search through (splitted)
        """
        return [-2] + [i for i in range(len(split_string)) if split_string[i] in {"<=", '<', '=', '>', ">="}]

    def read_bounds(self, bounds_start: int, generals_start: int, binaries_start: int) -> None:
        """ Reads the bounds of the content into a list of dictionaries

        Parameters
        ----------
        bounds_start:
            Index of start of bounds
        generals_start:
            Index of start of generals
        binaries_start:
            Index of start of binaries
        """
        raw_bounds = self.content[bounds_start + 1:(generals_start or binaries_start or -1)]
        # since bounds are just "variable sense value"
        for raw_bound in raw_bounds:
            split_bound = raw_bound.split(' ')
            if len(split_bound) == 3:
                try:
                    float(split_bound[0])
                    # it's the number first, it's 5 <= x
                    self.bounds_list.append({'variable': split_bound[2],
                                             'low_bound': float(split_bound[0]),
                                             'up_bound': None})
                except ValueError:
                    # it's the variable first
                    if split_bound[1] == '=':  # it's x = 5
                        self.bounds_list.append({'variable': split_bound[0],
                                                 'low_bound': float(split_bound[2]),
                                                 'up_bound': float(split_bound[2])})
                    else:  # it's x <= 5
                        self.bounds_list.append({'variable': split_bound[0],
                                                 'low_bound': None,
                                                 'up_bound': float(split_bound[2])})
            else:  # length is 5 so it's 5 <= x <= 7
                self.bounds_list.append({'variable': split_bound[2],
                                         'low_bound': float(split_bound[0]),
                                         'up_bound': float(split_bound[4])})

    def get_var_type(self, string: str) -> VarType:
        """ Gets the type of a variable by name

        Parameters
        ----------
        string:
            The name of the variable
        """
        if string in self.binaries_list:
            return VarType.Binary
        if string in self.generals_list:
            return VarType.Integer
        return VarType.Continuous

    def get_var_up_bound(self, string: str) -> Optional[Numeric]:
        """ Gets the upper bound of a variable by name

        Parameters
        ----------
        string:
            The name of the variable
        """
        if self.bounds_list:
            if string in set(bound['variable'] for bound in self.bounds_list):
                return [bound['up_bound'] for bound in self.bounds_list if bound['variable'] == string][0]
        return None

    def get_var_low_bound(self, string: str) -> Optional[Numeric]:
        """ Gets the lower bound of a variable by name

        Parameters
        ----------
        string: str
            The name of the variable
        """
        if self.bounds_list:
            if string in set(bound['variable'] for bound in self.bounds_list):
                return [bound['low_bound'] for bound in self.bounds_list if bound['variable'] == string][0]
        return None

    def create_constraint(self, constraint: Mapping[str, Union[Numeric, str]]) -> LpConstraint:
        """ Creates a linear constraint from a dictionary

        Parameters
        ----------
        constraint: Mapping[str, Union[Numeric, str]]
            Dictionary representing the constraint
        """
        rhs_expression = LpExpression(constant=constraint['rhs'])
        lhs_expression = LpExpression(
            expression={self.dictionary_of_variables[name]: constraint['lhs'][name] for name in constraint['lhs'].keys()})
        sense = {'<=': 'leq', '>=': 'geq', '=': 'eq'}[constraint['sense']]
        name = constraint['name']

        return LpConstraint(lhs_expression, sense, rhs_expression, name)

    def read_lp(self, lp_file: str) -> LpProblem:
        """ Reads a text file of an LP (written by PuLP or Flippy) into a Flippy LpProblem

        Parameters
        ----------
        lp_file:
            filepath for the LP file to read
        """
        self.extract_content(lp_file)
        self.verify()

        # these may not be there but grab if they are
        bounds_start = self.lst_find(self.content, 'Bounds')
        generals_start = self.lst_find(self.content, 'Generals')
        binaries_start = self.lst_find(self.content, 'Binaries')

        # if there are contraints:
        constraints_string_split = ' '.join(self.content[self.obj_end+1:bounds_start]).strip().split(' ')
        constraint_list = []

        breaks = self.find_breaks(constraints_string_split)

        # iterate through each constraint and capture
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
        self.bounds_list = []
        if bounds_start:
            self.read_bounds(bounds_start, generals_start, binaries_start)

        # if there are Generals:
        self.generals_list = []
        if generals_start:
            generals_string = ' '.join(self.content[generals_start+1:(binaries_start or -1)]).strip()
            self.generals_list = generals_string.split(' ')
        # if there are Binaries:
        self.binaries_list = []
        if binaries_start:
            binaries_string = ' '.join(self.content[binaries_start+1:-1]).strip()
            self.binaries_list = binaries_string.split(' ')

        obj_string = ' '.join(self.content[self.obj_start:self.obj_end]).strip()
        obj_name = obj_string.split(' ')[0][:-1]
        obj = mathify_expression(obj_string.split(' ')[1:])

        variable_names = set(obj.keys()).union(*[constraint['lhs'].keys() for constraint in constraint_list])

        self.dictionary_of_variables = {name: LpVariable(name, var_type=self.get_var_type(name), up_bound=self.get_var_up_bound(name),
                                                         low_bound=self.get_var_low_bound(name)) for name in variable_names}
        objective = LpObjective(name=obj_name, expression={self.dictionary_of_variables[name]: obj[name] for name in obj},
                                sense=self.problem_sense)
        constraints = []

        for constraint in constraint_list:
            constraints.append(self.create_constraint(constraint))

        return LpProblem(self.problem_name, objective, constraints)
