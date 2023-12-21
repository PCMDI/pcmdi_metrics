import re
from copy import copy


def sort_human(input_list: list[str]) -> list:
    """Sort list by natual order

    Parameters
    ----------
    input_list : list
        input list

    Returns
    -------
    list
        sorted list
    """
    lst = copy(input_list)

    def convert(text):
        return int(text) if text.isdigit() else text

    def alphanum(key):
        return [convert(c) for c in re.split("([0-9]+)", key)]

    lst.sort(key=alphanum)
    return lst
