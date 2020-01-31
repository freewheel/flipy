import os
import tempfile
import platform
import subprocess

from flipy.lp_problem import LpProblem
from flipy.solvers.base_solver import SolutionStatus


class SolverError(Exception):
    pass


class CBCSolver:
    """ A class for interfacing with cbc to solve LPs"""

    STATUS_MAPPING = {
        'Optimal': SolutionStatus.Optimal,
        'Infeasible': SolutionStatus.Infeasible,
        'Integer': SolutionStatus.Infeasible,
        'Unbounded': SolutionStatus.Unbounded,
        'Stopped': SolutionStatus.NotSolved
    }

    CBC_BIN_PATH = {
        ('Linux', '32bit'): 'bin/cbc-linux64/cbc',
        ('Linux', '64bit'): 'bin/cbc-linux64/cbc',
        ('Darwin', '64bit'): 'bin/cbc-osx/cbc',
        ('Windows', '32bit'): 'bin/cbc-win32/cbc.exe',
        ('Windows', '64bit'): 'bin/cbc-win64/cbc.exe',
    }

    def __init__(self) -> None:
        """ Initialize the solver """
        self.bin_path = os.getenv('CBC_SOLVER_BIN', self._find_cbc_binary())

    @classmethod
    def _find_cbc_binary(cls) -> str:
        """ Find the CBC binary path based on the current system and architecture

        Returns
        -------
        str
        """
        if 'CBC_SOLVER_BIN' in os.environ:
            return os.getenv('CBC_SOLVER_BIN')
        system = platform.system()
        arch, _ = platform.architecture()
        try:
            bin_path = cls.CBC_BIN_PATH[system, arch]
        except KeyError:
            raise SolverError(f'no CBC solver found for system {system} {arch}, '
                              'please set the solver path manually with environment variable \'CBC_SOLVER_BIN\'')
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), bin_path)

    def solve(self, lp_problem: LpProblem) -> SolutionStatus:
        """ Form and solve the lp

        Parameters
        ----------
        lp_problem:
            The Flipy LP to solve
        """
        temp_dir = tempfile.TemporaryDirectory()
        lp_file_path = os.path.join(temp_dir.name, 'problem.lp')
        solution_file_path = os.path.join(temp_dir.name, 'solution.sol')

        with open(lp_file_path, 'w') as f:
            lp_problem.write_lp(f)

        self.call_cbc(f.name, solution_file_path)

        if not os.path.exists(solution_file_path):
            raise SolverError("Error while trying to solve the problem")

        return self.read_solution(solution_file_path, lp_problem)

    def call_cbc(self, lp_file_path: str, solution_file_path: str):
        """ Call cbc to solve an lp file

        Parameters
        ----------
        lp_file_path
            The location of the lp to solve
        solution_file_path:
            Where to record the solution
        """
        pipe = open(os.devnull, 'w')
        args = [self.bin_path, lp_file_path, 'branch', 'printingOptions', 'all', 'solution', solution_file_path]
        coin_proc = subprocess.Popen(args, stderr=pipe, stdout=pipe)
        if coin_proc.wait() != 0:
            raise SolverError(f"Error while trying to execute {self.bin_path}")
        pipe.close()

    @classmethod
    def read_solution(cls, filename: str, lp_problem: LpProblem) -> SolutionStatus:
        """ Read in variable values from a saved solution file

        Parameters
        ----------
        filename:
            The solution to read
        lp_problem:
            The Flipy object to set the variable values in
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
                line = line.split()
                if line[0] == '**':
                    line = line[1:]
                var_name = line[1]
                val = line[2]
                if var_name in values:
                    values[var_name] = float(val)

        for var in lp_problem.lp_variables.values():
            var.set_value(values[var.name])
        for constraint in lp_problem.lp_constraints.values():
            if constraint.slack:
                constraint.slack_variable.set_value(values[constraint.slack_variable.name])
        return status
