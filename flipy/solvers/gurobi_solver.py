import os
import tempfile
from typing import Optional, List

import gurobipy  # pylint: disable=import-error

from flipy.lp_problem import LpProblem
from flipy.lp_variable import VarType, LpVariable
from flipy.lp_objective import Maximize
from flipy.solvers.base_solver import SolutionStatus
from flipy.utils import Numeric

# Disable gurobipy no-member linting
# pylint: disable=no-member


class GurobiSolver:
    """ A class for interfacing with gurobi to solve LPs """

    STATUS_MAPPING = {
        gurobipy.GRB.OPTIMAL: SolutionStatus.Optimal,
        gurobipy.GRB.INFEASIBLE: SolutionStatus.Infeasible,
        gurobipy.GRB.INF_OR_UNBD: SolutionStatus.Infeasible,
        gurobipy.GRB.UNBOUNDED: SolutionStatus.Unbounded,
        gurobipy.GRB.ITERATION_LIMIT: SolutionStatus.NotSolved,
        gurobipy.GRB.NODE_LIMIT: SolutionStatus.NotSolved,
        gurobipy.GRB.TIME_LIMIT: SolutionStatus.NotSolved,
        gurobipy.GRB.SOLUTION_LIMIT: SolutionStatus.NotSolved,
        gurobipy.GRB.INTERRUPTED: SolutionStatus.NotSolved,
        gurobipy.GRB.NUMERIC: SolutionStatus.NotSolved
    }

    def __init__(self, mip_gap: float = 0.1, timeout: Optional[int] = None, enable_logging: bool = False) -> None:
        """ Initialize the solver

        Parameters
        ----------
        mip_gap:
            The gap used to determine when a solution to the mip has been found
        timeout:
            The time allowed for solving
        enable_logging:
            Whether gurobi logs should be shown
        """
        self.mip_gap = mip_gap
        self.timeout = timeout
        gurobipy.setParam("OutputFlag", enable_logging)

    def solve(self, lp_problem: LpProblem) -> SolutionStatus:
        """ Form and solve the LP, set the variables to their solution values.

        Raises
        ------
        Exception
            Raised when lp_problem is not an instance of LpProblem

        Parameters
        ----------
        lp_problem:
            The LP to solve

        Returns
        -------
        flipy.SolutionStatus
            The status of the solution
        """
        model = gurobipy.Model(lp_problem.name)

        model.setParam('MIPGap', self.mip_gap)
        if self.timeout is not None:
            model.setParam('TimeLimit', self.timeout)

        if lp_problem.lp_objective and lp_problem.lp_objective.sense == Maximize:
            model.setAttr("ModelSense", -1)

        if not isinstance(lp_problem, LpProblem):
            raise Exception('%s is not an LpProblem' % lp_problem)

        if lp_problem.lp_objective.sense == Maximize:
            model.setAttr("ModelSense", -1)

        variables = list(lp_problem.lp_variables.values())
        self.add_variables(variables, model)
        self.add_constraints(lp_problem, model)
        model.optimize()
        self.retrieve_values(lp_problem, variables, model)
        return self.STATUS_MAPPING[model.Status]

    @staticmethod
    def add_variable(var: LpVariable, obj_coef: Numeric, model: gurobipy.Model) -> None:
        """ Add a variable to the LP

        Parameters
        ----------
        var:
            The linear variable to add
        obj_coef:
            The coefficient of the linear variable in the objective
        model:
            The gurobi model to add the variable to
        """
        low_bound = var.low_bound
        if low_bound is None:
            low_bound = -gurobipy.GRB.INFINITY
        up_bound = var.up_bound
        if up_bound is None:
            up_bound = gurobipy.GRB.INFINITY
        if var.var_type == VarType.Continuous:
            var_type = gurobipy.GRB.CONTINUOUS
        else:
            var_type = gurobipy.GRB.INTEGER
        var.solver_var = model.addVar(low_bound, up_bound, vtype=var_type, obj=obj_coef, name=var.name)

    def add_variables(self, lp_variables: List[LpVariable], model: gurobipy.Model) -> None:
        """ Add the variables in a Flipy LpProblem to a gurobi model

        Parameters
        ----------
        lp_variables:
            The Flipy object to grab the variables from
        model:
            The gurobi model to add the variables to
        """
        for var in lp_variables:
            self.add_variable(var, var.obj_coeff, model)
        model.update()

    def add_constraints(self, lp_problem: LpProblem, model: gurobipy.Model) -> None:
        """ Add the constraints in a Flipy LpProblem to a gurobi model

        Parameters
        ----------
        lp_problem:
            The Flipy object to grab the constraints from
        model:
            The gurobi model to add the constraints to
        """
        for name, constraint in lp_problem.lp_constraints.items():
            lhs_expr = [(coef, var.solver_var) for var, coef in constraint.lhs.expr.items()]
            if constraint.slack:
                self.add_variable(constraint.slack_variable,
                                  (-1 if lp_problem.lp_objective.sense == Maximize else 1) * constraint.slack_penalty,
                                  model)
                lhs_expr += [((-1 if constraint.sense == 'leq' else 1), constraint.slack_variable.solver_var)]
            lhs_expr = gurobipy.LinExpr(lhs_expr)
            lhs_expr.addConstant(constraint.lhs.const)
            rhs_expr = gurobipy.LinExpr([(coef, var.solver_var) for var, coef in constraint.rhs.expr.items()])
            rhs_expr.addConstant(constraint.rhs.const)
            if constraint.sense.lower() == 'leq':
                relation = gurobipy.GRB.LESS_EQUAL
            elif constraint.sense.lower() == 'geq':
                relation = gurobipy.GRB.GREATER_EQUAL
            else:
                relation = gurobipy.GRB.EQUAL
            constraint.solver_constraint = model.addConstr(lhs_expr, relation, rhs_expr, name)
        model.update()

    @staticmethod
    def retrieve_values(lp_problem: LpProblem, lp_variables: List[LpVariable], model: gurobipy.Model) -> None:
        """ Extract the value of variables from the gurobi model and set them into the Flipy objects

        Parameters
        ----------
        lp_problem:
            The Flipy object into which the variable values will be set
        lp_variables:
            A list of LpVariables of the problem
        model:
            The gurobi model to grab the variable values from
        """
        try:
            var_name_to_values = dict(
                zip(
                    model.getAttr(gurobipy.GRB.Attr.VarName, model.getVars()),
                    model.getAttr(gurobipy.GRB.Attr.X, model.getVars())))
            for var in lp_variables:
                var.set_value(var_name_to_values[var.name])
            for constraint in lp_problem.lp_constraints.values():
                if constraint.slack:
                    constraint.slack_variable.set_value(var_name_to_values[constraint.slack_variable.name])
        except (gurobipy.GurobiError, AttributeError):
            pass


class GurobiFileSolver(GurobiSolver):
    """ A class for interfacing with gurobi to solve LPs

    Instead of building the model by calling Gurobi APIs, thie solver writes an LP file to a local
    temporary folder, and calls `gurobipy.read` to build the model from the file.
    """

    def solve(self, lp_problem: LpProblem) -> SolutionStatus:
        """ Form and solve the LP, set the variables to their solution values.

        Raises
        ------
        Exception
            Raised when lp_problem is not an instance of LpProblem

        Parameters
        ----------
        lp_problem:
            The LP to solve

        Returns
        -------
        flipy.SolutionStatus
            The status of the solution
        """
        temp_dir = tempfile.TemporaryDirectory()
        problem_file_path = os.path.join(temp_dir.name, 'problem.lp')
        solution_file_path = os.path.join(temp_dir.name, 'solution.sol')

        with open(problem_file_path, 'w') as f:
            lp_problem.write_lp(f)

        model = gurobipy.read(problem_file_path)

        model.setParam('MIPGap', self.mip_gap)
        if self.timeout is not None:
            model.setParam('TimeLimit', self.timeout)

        model.optimize()
        model.write(solution_file_path)
        self.read_solution(solution_file_path, lp_problem)
        return self.STATUS_MAPPING[model.Status]

    @classmethod
    def read_solution(cls, filename: str, lp_problem: LpProblem) -> SolutionStatus:
        """ Read in variable values from a saved solution file

        Parameters
        ----------
        filename:
            The solution to read
        lp_problem:
            The Flipy object to set the variable values in

        Returns
        -------
        flipy.SolutionStatus
            The status of the solution
        """
        values = {}
        for var in lp_problem.lp_variables.values():
            values[var.name] = 0
        for constraint in lp_problem.lp_constraints.values():
            if constraint.slack:
                values[constraint.slack_variable.name] = 0

        with open(filename) as f:
            status_str = f.readline().split()[0]
            status = cls.STATUS_MAPPING.get(status_str, SolutionStatus.NotSolved)
            for line in f:
                if len(line) <= 2:
                    break
                if line.startswith('#'):
                    continue
                line = line.split()
                if line[0] == '**':
                    line = line[1:]
                var_name = line[0]
                val = line[1]
                if var_name in values:
                    values[var_name] = float(val)

        for var in lp_problem.lp_variables.values():
            var.set_value(values[var.name])
        for constraint in lp_problem.lp_constraints.values():
            if constraint.slack:
                constraint.slack_variable.set_value(values[constraint.slack_variable.name])
        return status
