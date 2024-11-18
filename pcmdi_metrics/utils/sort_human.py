import re
from copy import copy


def sort_human(input_list: list[str]) -> list:
    """
    Sort a list of strings in natural order.

    This function sorts a list of strings using a natural sorting algorithm,
    which means that strings containing numbers are sorted in a way that
    respects numerical order within the string.

    Parameters
    ----------
    input_list : list of str
        The input list of strings to be sorted.

    Returns
    -------
    list of str
        A new list containing the input strings sorted in natural order.

    Notes
    -----
    The natural sorting algorithm used in this function considers the
    numerical values within strings when determining the sort order. For
    example, "file2" will be sorted before "file10".

    Examples
    --------
    >>> from pcmdi_metrics.utils import sort_human
    >>> sort_human(['file1', 'file10', 'file2'])
    ['file1', 'file2', 'file10']

    >>> sort_human(['1.txt', '10.txt', '2.txt', 'foo.txt'])
    ['1.txt', '2.txt', '10.txt', 'foo.txt']

    """
    lst = copy(input_list)

    def convert(text):
        return int(text) if text.isdigit() else text

    def alphanum(key):
        return [convert(c) for c in re.split("([0-9]+)", key)]

    lst.sort(key=alphanum)
    return lst
