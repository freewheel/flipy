from typing import Union, List

# The default length of line allowed in LP files
LpCplexLPLineSize = 78

Numeric = Union[int, float]


def _count_characters(line: List[str]) -> int:
    """ Counts the number of characters in a list of strings

    Parameters
    ----------
    line:
        The line to count the characters of
    """
    return sum(len(t) for t in line)
