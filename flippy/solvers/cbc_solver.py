import os
import tempfile
import subprocess

from flippy.lp_problem import LpProblem
from flippy.solvers.base_solver import SolutionStatus


class SolverError(Exception):
    pass


STATUS_MAPPING = {
    'Optimal': SolutionStatus.Optimal,
    'Infeasible': SolutionStatus.Infeasible,
    'Integer': SolutionStatus.Infeasible,
    'Unbounded': SolutionStatus.Unbounded,
    'Stopped': SolutionStatus.NotSolved
}


class CoinSolver:

    def __init__(self, cbc_bin_path='cbc'):
        self.bin_path = os.getenv('CBC_SOLVER_BIN', cbc_bin_path)

    def solve(self, lp_problem: LpProblem) -> SolutionStatus:
        temp_dir = tempfile.TemporaryDirectory()
        lp_file_path = os.path.join(temp_dir.name, 'problem.lp')
        solution_file_path = os.path.join(temp_dir.name, 'solution.sol')

        with open(lp_file_path, 'w') as f:
            lp_problem.write_lp(f)

        self.call_cbc(f.name, solution_file_path)

        if not os.path.exists(solution_file_path):
            raise SolverError("Error while trying to solve the problem")

        return self.read_solution(solution_file_path, lp_problem)

    def call_cbc(self, lp_file_path, solution_file_path):
        pipe = open(os.devnull, 'w')
        args = [self.bin_path, lp_file_path, 'branch', 'printingOptions', 'all', 'solution', solution_file_path]
        coin_proc = subprocess.Popen(args, stderr=pipe, stdout=pipe)
        if coin_proc.wait() != 0:
            raise SolverError(f"Error while trying to execute {self.bin_path}")
        pipe.close()

    @staticmethod
    def read_solution(filename, lp_problem):
        values = {}
        for var in lp_problem.lp_variables.values():
            values[var.name] = 0
        for constraint in lp_problem.lp_constraints.values():
            if constraint.slack:
                values[constraint.slack_variable.name] = 0

        with open(filename) as f:
            status_str = f.readline().split()[0]
            status = STATUS_MAPPING.get(status_str, SolutionStatus.NotSolved)
            for line in f:
                if len(line) <= 2:
                    break
                line = line.split()
                if line[0] == '**':
                    line = line[1:]
                var_name = line[1]
                val = line[2]
                if var_name in values:
                    values[var_name] = float(val)

        for var in lp_problem.lp_variables.values():
            var._value = values[var.name]
        for constraint in lp_problem.lp_constraints.values():
            if constraint.slack:
                constraint.slack_variable._value = values[constraint.slack_variable.name]
        return status
