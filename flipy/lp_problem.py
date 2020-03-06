from typing import Optional, List

from flipy.lp_variable import LpVariable, VarType
from flipy.lp_constraint import LpConstraint
from flipy.lp_objective import LpObjective, Minimize


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

        Raises
        ------
        TypeError
            If `lp_variable` is not an `LpVariable` object
        NameError
            If the name of `lp_variable` conflicts with an existing variable in the problem

        Parameters
        ----------
        lp_variable:
            The variable to add
        """
        if not isinstance(lp_variable, LpVariable):
            raise TypeError('%s is not an LpVariable' % lp_variable)
        if self.lp_variables.get(lp_variable.name, lp_variable) != lp_variable:
            raise NameError('LP variable name %s conflicts with an existing LP variable' % lp_variable.name)
        self.lp_variables[lp_variable.name] = lp_variable

    def set_objective(self, lp_objective: LpObjective) -> None:
        """ Sets the objective of the LP problem and adds all variables. Raises error if already has an objective.

        Raises
        ------
        TypeError
            If `lp_objective` is not an `LpObjective` object
        Exception
            If the objective is already set in the problem

        Parameters
        ----------
        lp_objective:
            The objective to set
        """
        if not isinstance(lp_objective, LpObjective):
            raise TypeError('%s is not an LpObjective' % lp_objective)
        if self.lp_objective:
            raise Exception('LP objective is already set')
        for var, coeff in lp_objective.expr.items():
            self.add_variable(var)
            var.set_obj_coeff(coeff)
        self.lp_objective = lp_objective

    def add_constraint(self, lp_constraint: LpConstraint) -> None:
        """ Adds a constraint to the LP problem and adds all variables. Raises error if namespace conflict.

        Raises
        ------
        TypeError
            If `lp_constraint` is not an `LpConstraint` object
        NameError
            If the name of `lp_constraint` conflicts with an existing constraint in the problem

        Parameters
        ----------
        lp_constraint:
            The constraint to add
        """
        if not isinstance(lp_constraint, LpConstraint):
            raise TypeError('%s is not an LpConstraint' % lp_constraint)
        if self.lp_constraints.get(lp_constraint.name, lp_constraint) != lp_constraint:
            raise NameError('LP constraint name %s conflicts with an existing LP constraint' % lp_constraint.name)
        self.lp_constraints[lp_constraint.name] = lp_constraint
        for var in lp_constraint.lhs.expr.keys():
            self.add_variable(var)
        for var in lp_constraint.rhs.expr.keys():
            self.add_variable(var)

    @staticmethod
    def _group_terms(terms, max_line_length=80):
        """ Groups terms into list of lines. Each line doesn't exceed certain width.

        Parameters
        ----------
        terms: list(str)
            Lift of terms in string
        max_line_length: int
            Maximum length of a line

        Returns
        -------
        list(str)
            List of lines
        """
        lines = []

        line_len = 0
        start_i = 0
        for i, term in enumerate(terms):
            if line_len + len(term) >= max_line_length:
                lines.append(' '.join(terms[start_i:i]))
                start_i = i
                line_len = 0
            line_len += len(term) + 1
            if i == len(terms) - 1:
                lines.append(' '.join(terms[start_i:]))

        return lines

    def write_lp(self, buffer):
        """ Writes the problem in an LP format to a buffer

        Raises
        ------
        Exception
            If the problem doesn't have an objective

        Parameters
        ----------
        buffer: buffer-like
            A buffer-like object with a `write` method
        """
        if not self.lp_objective:
            raise Exception('No objective')

        buffer.write(f'\\* {self.name} *\\\n')
        if self.lp_objective.sense == Minimize:
            buffer.write('Minimize\n')
        else:
            buffer.write('Maximize\n')

        objective_name = self.lp_objective.name if self.lp_objective.name else "OBJ"

        obj_slack_expr = {constraint.slack_variable: constraint.slack_penalty * (1 if self.lp_objective.sense == Minimize else -1)
                          for constraint in self.lp_constraints.values() if constraint.slack}

        terms = [f'{objective_name}:'] + self.lp_objective.to_lp_terms(slack=obj_slack_expr)

        obj_lines = self._group_terms(terms)

        for obj_line in obj_lines:
            buffer.write(obj_line)
            buffer.write('\n')

        buffer.write("Subject To\n")

        constraints = sorted(self.lp_constraints.keys())
        for con in constraints:
            constraint = self.lp_constraints[con]
            terms = [f'{con}:'] + constraint.to_lp_terms()
            cons_lines = self._group_terms(terms)
            for line in cons_lines:
                buffer.write(line)
                buffer.write('\n')

        sorted_lp_variables = sorted(self.lp_variables.values(), key=lambda v: v.name)

        # Bounded variables
        bounded_vars = [var for var in sorted_lp_variables if not var.is_positive_free()]
        if bounded_vars:
            buffer.write("Bounds\n")
            for var in bounded_vars:
                buffer.write(f"{var.to_lp_str()}\n")

        # Integer non-binary variables
        integer_vars = [
            var for var in sorted_lp_variables if (var.var_type is VarType.Integer)
        ]
        if integer_vars:
            buffer.write("Generals\n")
            for var in integer_vars:
                buffer.write(f"{var.name}\n")

        # Binary variables
        binary_vars = [var for var in sorted_lp_variables if var.var_type is VarType.Binary]
        if binary_vars:
            buffer.write("Binaries\n")
            for var in binary_vars:
                buffer.write(f"{var.name}\n")

        buffer.write("End\n")
