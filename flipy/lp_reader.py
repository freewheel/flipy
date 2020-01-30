import os
import io
import re
from collections import defaultdict, namedtuple
from typing import Union, Optional, Mapping, List, Tuple, Iterable, IO, TextIO

from flipy.utils import Numeric, INF
from flipy.lp_problem import LpProblem
from flipy.lp_constraint import LpConstraint
from flipy.lp_expression import LpExpression
from flipy.lp_variable import VarType, LpVariable
from flipy.lp_objective import LpObjective, Minimize, Maximize


class LpReader:
    """ A class for reading lp files """
    _numeric_regex_pattern = re.compile(r'^ \s* [-+]? \s* (?: (?: \d* \. \d+ ) | (?: \d+ \.? ) )(?: [Ee] [+-]? \d+ ) ?',
                                        re.VERBOSE)
    _sense_mapping = {'<=': 'leq', '=<': 'leq', '>=': 'geq', '=>': 'geq', '<': 'lt', '>': 'gt', '=': 'eq'}

    _sense_reverse_mapping = {'leq': 'geq', 'geq': 'leq', 'lt': 'gt', 'gt': 'lt', 'eq': 'eq'}

    @classmethod
    def _parse_term(cls, term: str) -> Tuple[str, Numeric]:
        """ Parse a CPLEX format term into a tuple consisting of a variable name and a coefficient

        Examples
        --------
        >>> LpReader._parse_term('3 x')
        ('x', 3.0)
        >>> LpReader._parse_term('- 3 x')
        ('x', -3.0)

        Raises
        ------
        NameError
            If one of the variables doesn't have a valid name

        Parameters
        ----------
        term: str
            A CPLEX format term like "x", "3x", "-3x"

        Returns
        -------
        str
            The parsed variable name
        float
            The coefficient of the variable
        """
        term = term.strip()

        match = re.search(cls._numeric_regex_pattern, term)

        if match:
            coeff = float(match.group().replace(' ', ''))
            _, coeff_end = match.span()
        else:
            coeff = 1
            coeff_end = 0

        var = term[coeff_end:].strip()

        if not var:
            return None, coeff

        if '0' < var[0] < '9' or var[0] == '.':
            raise NameError(f"variable '{var}' does not have a valid name: "
                            "A variable name should not begin with a number or a period")

        if ' ' in var:
            raise NameError(f"variable '{var}' does not have a valid name: "
                            "A variable name should not have whitespaces")

        for char in var:
            # ASCII hack: https://en.wikipedia.org/wiki/ASCII
            # http://lpsolve.sourceforge.net/5.0/CPLEX-format.htm
            if char < '!' or char > '~' or char in ('*', '+', '-', '\\', ']', '^', ':', '[', '<', '=', '>'):
                raise NameError(f"variable '{var}' does not have a valid name")

        return var, coeff

    @classmethod
    def _mathify_expression(cls, expr_str: str) -> Tuple[Mapping[str, Numeric], Numeric]:
        """ Convert an LP format expression in to a dictionary

        >>> LpReader._mathify_expression('3x + 4y - 5')
        ({'x': 3.0, 'y': 4.0}, -5.0)
        >>> LpReader._mathify_expression('-5')
        ({}, -5.0)

        Parameters
        ----------
        expr_str: str
            A CPLEX format expression like "3x + 4y - 5"

        Returns
        -------
        dict
            The expression in which the key is the variable name and value is the coefficient
        float
            The constant added to the expression
        """
        expr = defaultdict(int)
        const = 0
        expr_str = expr_str.strip()
        if not expr_str:
            return expr, const

        tokens = [token.strip() for token in re.split(r'(-|\+)', expr_str)]

        sign = 1

        for token in tokens:
            if not token:
                continue
            if token == '+':
                sign = 1
            elif token == '-':
                sign = -1
            else:
                var, coeff = cls._parse_term(token)
                if var is None:
                    const += sign * coeff
                else:
                    expr[var] += sign * coeff

        return dict(expr), const

    @classmethod
    def _remove_comments(cls, content: str) -> str:
        """ Remove the comments from a string

        >>> LpReader._remove_comments(r' 3x + y \\ this is a comment section \\ < 5 ')
        ' 3x + y  < 5 '
        >>> LpReader._remove_comments(r' 3x + y \\ this is a comment section')
        ' 3x + y '

        Parameters
        ----------
        content: str
            Any string that may contain one or more CPLEX format comment section starts with '/'

        Returns
        -------
        str
            The original string with CPLEX format comments removed
        """
        content = re.sub(re.compile(r"\\.*?\\", re.DOTALL), "",
                         content)  # remove all occurrences of \COMMENT\ from line
        content = re.sub(re.compile(r"\\.*?$"), "",
                         content)  # remove all occurrence single-backslash comments (\COMMENT) from string
        return content

    @staticmethod
    def _search_keywords(content: str, keywords: Iterable[str]) -> Tuple[str, int, int]:
        """ Search multiple keywords in a string case insensitively, return the first match

        Example:
        >>> LpReader._search_keywords("FreeWheel Linear Programming Interface for Python", ['python', 'java'])
        ('Python', 43, 49)

        Parameters
        ----------
        content: str
            The input string to be searched
        keywords: list(str)
            The keyword list to search for

        Returns
        -------
        str
            The matched keyword
        int
            Start index of the matched keyword
        int
            End index of the matched keyword

        Raises
        ------
        ValueError
            When none of the keywords is found in the content, a ValueError is raised
        """
        sense_pattern = re.compile('|'.join(rf'\b{re.escape(keyword)}\b' for keyword in keywords), re.IGNORECASE)
        match = sense_pattern.search(content)
        return match.group(), match.start(), match.end()

    @classmethod
    def _split_content_by_sections(cls, content: str) -> Tuple[bool, Mapping[str, str]]:
        """ Split a CPLEX LP file into multiple sections

        It searches for the keywords of objective, constraints, bounds, generals, binaries, end and split
        the content by section

        Raises
        ------
        ValueError
            When the lp file is not in a valid LP file format

        Parameters
        ----------
        content
            The content of a CPLEX LP file

        Returns
        -------
        bool
            True if the problem is a maximization problem False otherwise
        dict(str -> str)
            Mapping from section names to section content
        """
        keywords = {
            'objective': ('minimize', 'maximize', 'minimum', 'maximum', 'min', 'max'),
            'constraints': ('subject to', 'such that', 'st', 's.t.', 'st.'),
            'bounds': ('bounds', 'bound'),
            'generals': ('general', 'generals', 'gen'),
            'binaries': ('binary', 'binaries', 'bin'),
            'end': ('end',)
        }

        sections = []
        is_maximize = None

        Section = namedtuple('Section', ('name', 'keyword_start', 'keyword_end'))

        for section_name, keywords in keywords.items():
            try:
                match, keyword_start, keyword_end = cls._search_keywords(content, keywords)
                if section_name == 'objective':
                    is_maximize = match.lower().startswith('max')
                sections.append(Section(section_name.lower(), keyword_start, keyword_end))
            except AttributeError:
                pass

        if is_maximize is None:
            raise ValueError('file must start with an objective')

        sections.sort(key=lambda x: x.keyword_start)  # sort by the start index of the section

        if sections[-1].name != 'end':
            raise ValueError('file must end with an "end" keyword')

        parsed_sections = {}

        for i in range(len(sections) - 1):
            section = sections[i]
            next_section = sections[i + 1]
            parsed_sections[section.name] = content[section.keyword_end:next_section.keyword_start].strip()

        return is_maximize, parsed_sections

    @classmethod
    def _find_problem_name(cls, content: str) -> str:
        """ Find the name of the problem by inferring the first comment section. If no comments are found,
        use "flipy_problem" as the problem name

        Parameters
        ----------
        content: str
            The problem content in a CPLEX LP format

        Returns
        -------
        str
            Inferred problem name
        """
        pattern = re.compile(r"(?<=\\)\s* [\w\s_]+ \s*(?=\\)", re.DOTALL)
        match = pattern.search(content)
        if match:
            return match.group().strip()
        return 'flipy_problem'

    @classmethod
    def _find_variable(cls, variables: Mapping[str, LpVariable], var_name: str) -> LpVariable:
        """ Find a variable from the variable dictionary, create a new one if not found

        Parameters
        ----------
        variables: dict(str -> LpVariable)
            Mapping from variable names to LpVariable

        var_name: str
            Name of the variable

        Returns
        -------
        LpVariable
            LpVariable found or created
        """

        try:
            return variables[var_name]
        except KeyError:
            var = LpVariable(var_name)
            variables[var_name] = var
            return var

    @classmethod
    def read(cls, obj: Union[str, IO, TextIO, io.StringIO]) -> LpProblem:
        """ Reads in an LP file and parse it into a flipy.LpProblem object

        Raises
        ------
        ValueError
            If `obj` is unreadable and is not a LP string

        Parameters
        ----------
        obj: str or buffer

        Returns
        -------
        LpProblem
            Parsed LpProblem based on the LP file
        """
        if hasattr(obj, 'read'):
            content = obj.read()
        elif isinstance(obj, (str, bytes)):
            content = obj
            try:
                if os.path.isfile(content):
                    with open(content, "rb") as f:
                        content = f.read()
            except (TypeError, ValueError):
                pass
        else:
            raise ValueError("Cannot read object of type %r" % type(obj).__name__)

        content = content.strip()

        problem_name = cls._find_problem_name(content)

        is_maximize, sections = cls._split_content_by_sections(cls._remove_comments(content))

        obj_name, obj_expr, obj_coeff = cls._parse_named_expression(sections['objective'])
        constraints = cls._parse_constraints(sections['constraints']) if 'constraints' in sections else []
        bounds = cls._parse_bounds(sections['bounds']) if 'bounds' in sections else []
        generals = cls._parse_generals(sections['generals']) if 'generals' in sections else []
        binaries = cls._parse_binaries(sections['binaries']) if 'binaries' in sections else []

        lp_variables = {}
        lp_objective = LpObjective(obj_name, constant=obj_coeff, sense=Maximize if is_maximize else Minimize)

        for obj_var_name, obj_coeff in obj_expr.items():
            obj_var = cls._find_variable(lp_variables, obj_var_name)
            lp_objective.expr[obj_var] = obj_coeff

        lp_constraints = []
        for constraint in constraints:
            lhs_expr = LpExpression()
            for var_name, cons_var_coeff in constraint['lhs'].items():
                var = cls._find_variable(lp_variables, var_name)
                lhs_expr.expr[var] = cons_var_coeff
            lhs_expr.const = constraint['lhs_const']

            rhs_expr = LpExpression()
            for var_name, cons_var_coeff in constraint['rhs'].items():
                var = cls._find_variable(lp_variables, var_name)
                rhs_expr.expr[var] = cons_var_coeff
            rhs_expr.const = constraint['rhs_const']

            lp_constraints.append(LpConstraint(lhs_expr, constraint['sense'], rhs_expr, name=constraint['name']))

        cls._parse_variables(lp_variables, bounds, generals, binaries)

        return LpProblem(problem_name, lp_objective=lp_objective, lp_constraints=lp_constraints)

    @classmethod
    def _parse_variables(cls, lp_variables: Mapping[str, LpVariable],
                         bounds: Mapping[str, Mapping[str, float]],
                         generals: List[str],
                         binaries: List[str]):
        """ Parses the information from bounds, generals and binaries

        Sets variable type, low_bound and up_bound accordingly

        Parameters
        ----------
        lp_variables: dict(str -> LpVariable)
            Variables of the problem
        bounds:
            Bounds parsed from cls._parse_bounds
        generals:
            General variable names parsed from cls._parse_generals
        binaries:
            Binary variable names parsed from cls._parse_binaries
        """
        for var_name, bound in bounds.items():
            var = cls._find_variable(lp_variables, var_name)
            if 'geq' not in bound or 'gt' not in bound:
                var.low_bound = 0
            for sense, const in bound.items():
                if sense == 'leq':
                    var.up_bound = const
                elif sense == 'geq':
                    var.low_bound = const
                elif sense == 'lt':
                    var.up_bound = const
                elif sense == 'gt':
                    var.low_bound = const
                elif sense == 'eq':
                    var.low_bound = const
                    var.up_bound = const

        for var_name in generals:
            var = cls._find_variable(lp_variables, var_name)
            var.var_type = VarType.Integer

        for var_name in binaries:
            var = cls._find_variable(lp_variables, var_name)
            var.var_type = VarType.Binary
            var.low_bound = 0
            var.up_bound = 1

    @classmethod
    def _parse_named_expression(cls, named_expr: str) -> Tuple[Optional[str], str, float]:
        """ Parse a named expression like "c1: 2 x1 + 3 x2 <= 5"

        Examples:
        --------
        >>> LpReader._parse_named_expression("c1: 2 x1 + 3 x2 + 5")
        ('c1', {'x1': 2.0, 'x2': 3.0}, 5.0)
        >>> LpReader._parse_named_expression("2 x1 + 3 x2 + 5")
        (None, {'x1': 2.0, 'x2': 3.0}, 5.0)

        Parameters
        ----------
        named_expr: str
            A CPLEX LP expression with a name at the beginning

        Returns
        -------
        str
            Name of the expression if given
        dict(str -> float)
            Mapping of variable names to coefficient
        float
            constant
        """
        named_expr = named_expr.replace('\n', ' ').strip()
        try:
            colon = named_expr.index(':')
            expr_name = named_expr[:colon].strip()
            expr_str = named_expr[colon + 1:].strip()
        except ValueError:
            expr_name = None
            expr_str = named_expr.strip()
        expr, const = cls._mathify_expression(expr_str)
        return expr_name, expr, const

    @classmethod
    def _parse_constraints(cls, constraints: str) -> List[Mapping[str, Union[str, float]]]:
        """ Parse the constraint section of a CPLEX LP format file

        Examples:
        --------
        >>> LpReader._parse_constraints("c1: x1 + 3 <= x2 - 5")
        [{'name': 'c1', 'lhs': {'x1': 1}, 'lhs_const': 3.0, 'sense': 'leq', 'rhs': {'x2': 1}, 'rhs_const': -5.0}]

        Raises
        ------
        ValueError
            If the constraint being parsed is not in a valid format

        Parameters
        ----------
        constraints: str
            The constraint section of a CPLEX LP format file

        Returns
        -------
        list(dict(str -> union(str, float)))
            Constraints in a list of dictionaries
        """

        parsed_constraints = []

        newline_pattern = re.compile(r'\n')

        sense_pattern = re.compile(r'|'.join(cls._sense_mapping.keys()))

        sense_matches = [match.span() for match in re.finditer(sense_pattern, constraints)]

        start = 0
        for i, _ in enumerate(sense_matches):
            sense_match = sense_matches[i]
            next_newline = newline_pattern.search(constraints, pos=sense_match[1])
            if next_newline:
                end = next_newline.start()
            else:
                end = len(constraints)

            try:
                cons_name, lhs, lhs_const = cls._parse_named_expression(constraints[start:sense_match[0]])
                sense = cls._sense_mapping[constraints[sense_match[0]:sense_match[1]]]
                rhs, rhs_const = cls._mathify_expression(constraints[sense_match[1]:end])
            except Exception:
                raise ValueError(f'constraint {constraints[start:end]} doesn\'t appear to be valid')

            parsed_constraints.append({
                'name': cons_name,
                'lhs': lhs,
                'lhs_const': lhs_const,
                'sense': sense,
                'rhs': rhs,
                'rhs_const': rhs_const
            })

            if next_newline:
                start = next_newline.end()
        return parsed_constraints

    @classmethod
    def _parse_bound_term(cls, term: str) -> Tuple[str, Union[str, float]]:
        """ Parse the type of a term in a bound section.

        A bound term can be either a variable, a constant, a sense indicator, or "free"

        Examples
        --------
        >>> LpReader._parse_bound_term('x1')
        ('variable', 'x1')
        >>> LpReader._parse_bound_term('15')
        ('constant', 15.0)
        >>> LpReader._parse_bound_term('1e3')
        ('constant', 1000.0)
        >>> LpReader._parse_bound_term('inf')
        ('constant', inf)
        >>> LpReader._parse_bound_term('-inf')
        ('constant', -inf)
        >>> LpReader._parse_bound_term('<=')
        ('sense', 'leq')
        >>> LpReader._parse_bound_term('free')
        ('free', 'free')

        Parameters
        ----------
        term: str
            A term in the above format

        Returns
        -------
        str
            Inferred term type
        union(str, float)
            Parsed term
        """
        try:
            return 'constant', float(term)
        except ValueError:
            pass
        try:
            return 'sense', cls._sense_mapping[term]
        except KeyError:
            pass
        if term == 'free':
            return 'free', 'free'
        return 'variable', term

    @classmethod
    def _parse_bounds(cls, bounds: str) -> Mapping[str, Mapping[str, float]]:
        """ Parse the boundary section of a CPLEX LP format file

        Parameters
        ----------
        bounds: str
            The content of the boundary section of the CPLEX LP file

        Returns
        -------
        dict(str -> dict(str -> float))
            Mapping from variable names to boundaries which is another mapping from sense indicators to float
        """
        terms = [term for term in bounds.replace('\n', ' ').split(' ') if term]

        parsed_bounds = defaultdict(dict)

        previous_term = None
        previous_term_type = None

        for i, term in enumerate(terms):
            term_type, parsed_term = cls._parse_bound_term(term)
            if term_type == 'free':
                parsed_bounds[previous_term]['leq'] = INF
                parsed_bounds[previous_term]['geq'] = -INF
            if term_type == 'sense':
                next_term = terms[i + 1]
                _, parsed_next_term = cls._parse_bound_term(next_term)
                if previous_term_type == 'variable':
                    parsed_bounds[previous_term][parsed_term] = parsed_next_term
                elif previous_term_type == 'constant':
                    parsed_bounds[parsed_next_term][cls._sense_reverse_mapping[parsed_term]] = previous_term
            previous_term = parsed_term
            previous_term_type = term_type

        return parsed_bounds

    @classmethod
    def _parse_generals(cls, generals: str) -> List[str]:
        """ Parse the general section of a CPLEX LP format file

        Parameters
        ----------
        generals
            The content of the general section of the CPLEX LP file

        Returns
        -------
        list(str)
            List of the variable names in the general section
        """
        return [general.strip() for general in generals.split('\n') if general.strip()]

    @classmethod
    def _parse_binaries(cls, binaries: str) -> List[str]:
        """ Parse the binaries section of a CPLEX LP format file

        Parameters
        ----------
        binaries
            The content of the binaries section of the CPLEX LP file

        Returns
        -------
        list(str)
            List of the variable names in the binaries section
        """
        return cls._parse_generals(binaries)
