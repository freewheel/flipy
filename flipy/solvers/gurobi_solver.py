from typing import Optional

import gurobipy

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

    def __init__(self, mip_gap: float = 0.1, timeout: Optional[int] = None) -> None:
        """ Initialize the solver

        Parameters
        ----------
        mip_gap:
            The gap used to determine when a solution to the mip has been found
        timeout:
            The time allowed for solving
        """
        self.mip_gap = mip_gap
        self.timeout = timeout

    def solve(self, lp_problem: LpProblem) -> SolutionStatus:
        """ Form and solve the LP, set the variables to their solution values.

        Parameters
        ----------
        lp_problem:
            The LP to solve
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

        self.add_variables(lp_problem, model)
        self.add_constraints(lp_problem, model)
        model.optimize()
        self.retrieve_values(lp_problem, model)
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

    def add_variables(self, lp_problem: LpProblem, model: gurobipy.Model) -> None:
        """ Add the variables in a Flipy LpProblem to a gurobi model

        Parameters
        ----------
        lp_problem:
            The Flipy object to grab the variables from
        model:
            The gurobi model to add the variables to
        """
        for _, var in lp_problem.lp_variables.items():
            self.add_variable(var, lp_problem.lp_objective.expr.get(var, 0), model)
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
            lhs_expr = [(coef, var.solver_var) for var, coef in constraint.lhs_expression.expr.items()]
            if constraint.slack:
                self.add_variable(constraint.slack_variable,
                                  (-1 if lp_problem.lp_objective.sense == Maximize else 1) * constraint.slack_penalty,
                                  model)
                lhs_expr += [((-1 if constraint.sense == 'leq' else 1), constraint.slack_variable.solver_var)]
            lhs_expr = gurobipy.LinExpr(lhs_expr)
            lhs_expr.addConstant(constraint.lhs_expression.const)
            rhs_expr = gurobipy.LinExpr(
                [(coef, var.solver_var) for var, coef in constraint.rhs_expression.expr.items()])
            rhs_expr.addConstant(constraint.rhs_expression.const)
            if constraint.sense.lower() == 'leq':
                relation = gurobipy.GRB.LESS_EQUAL
            elif constraint.sense.lower() == 'geq':
                relation = gurobipy.GRB.GREATER_EQUAL
            else:
                relation = gurobipy.GRB.EQUAL
            constraint.solver_constraint = model.addConstr(lhs_expr, relation, rhs_expr, name)
        model.update()

    @staticmethod
    def retrieve_values(lp_problem: LpProblem, model: gurobipy.Model) -> None:
        """ Extract the value of variables from the gurobi model and set them into the Flipy objects

        Parameters
        ----------
        lp_problem:
            The Flipy object into which the variable values will be set
        model:
            The gurobi model to grab the variable values from
        """
        try:
            for var in lp_problem.lp_variables.values():
                gurobi_var = model.getVarByName(var.name)
                var.set_value(gurobi_var.X)
            for constraint in lp_problem.lp_constraints.values():
                if constraint.slack:
                    gurobi_var = model.getVarByName(constraint.slack_variable.name)
                    constraint.slack_variable.set_value(gurobi_var.X)
        except (gurobipy.GurobiError, AttributeError):
            pass
