from collections import defaultdict
from typing import Any, DefaultDict


def tree() -> DefaultDict[Any, Any]:
    """
    Create a nested defaultdict with infinite depth.

    Returns:
    - DefaultDict[Any, Any]: A nested defaultdict that can be infinitely nested.

    Note:
    - This structure allows for arbitrary nesting without explicitly creating intermediate dictionaries.
    - Be cautious with very deep nesting as it may consume significant memory.

    Examples:
    --------
    >>> my_tree = tree()
    >>> my_tree['level1']['level2']['level3'] = 'value'
    >>> print(my_tree['level1']['level2']['level3'])  # Output: 'value'
    >>> print(my_tree['nonexistent']['key'])  # Creates nested dicts without error
    """
    return defaultdict(tree)
