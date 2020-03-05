import os
import tempfile
import platform
import subprocess
from typing import Optional

from flipy.lp_problem import LpProblem
from flipy.solvers.base_solver import SolutionStatus


class SolverError(Exception):
    """ Exception raised when a solver error is encountered """


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

    def __init__(self, mip_gap: float = 0.1, timeout: Optional[int] = None) -> None:
        """ Initialize the solver

        Parameters
        ----------
        mip_gap: float
            Relative MIP optimality gap.
            The solver will terminate (with an optimal result) when the gap between the lower and upper objective bound
            is less than MIPGap times the absolute value of the upper bound
            This can save some time if all you want to do is find a heuristic solution.
        timeout: int
            The time allowed for solving in seconds
        """
        self.bin_path = os.getenv('CBC_SOLVER_BIN', self._find_cbc_binary())
        self.mip_gap = mip_gap
        self.timeout = timeout

    @classmethod
    def _find_cbc_binary(cls) -> str:
        """ Find the CBC binary path based on the current system and architecture

        Raises
        ------
        SolverError
            If CBC solver encountered an error

        Returns
        -------
        str
            Path to the CBC binary file
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

        Raises
        ------
        SolverError
            If CBC solver encountered an error

        Parameters
        ----------
        lp_problem:
            The Flipy LP to solve

        Returns
        -------
        flipy.SolutionStatus
            The status of the solution
        """
        temp_dir = tempfile.TemporaryDirectory()
        lp_file_path = os.path.join(temp_dir.name, 'problem.lp')
        solution_file_path = os.path.join(temp_dir.name, 'solution.sol')

        with open(lp_file_path, 'w') as f:
            lp_problem.write_lp(f)

        self.call_cbc(f.name, solution_file_path)

        if not os.path.exists(solution_file_path):
            return SolutionStatus.NotSolved

        return self.read_solution(solution_file_path, lp_problem)

    def call_cbc(self, lp_file_path: str, solution_file_path: str):
        """ Call cbc to solve an lp file

        Raises
        ------
        SolverError
            If CBC solver encountered an error

        Parameters
        ----------
        lp_file_path:
            The location of the lp to solve
        solution_file_path:
            Where to record the solution
        """
        pipe = open(os.devnull, 'w')

        args = [self.bin_path, lp_file_path]
        if self.timeout:
            args.extend(['sec', str(self.timeout)])
        if self.mip_gap:
            args.extend(['ratio', str(self.mip_gap)])
        args.extend(['branch', 'printingOptions', 'all', 'solution', solution_file_path])

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
