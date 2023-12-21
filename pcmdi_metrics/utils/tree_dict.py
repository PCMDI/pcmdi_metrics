from collections import defaultdict


def tree():
    """
    Create a nested defaultdict with itself as the factory.

    Returns:
    - defaultdict: A nested defaultdict with a default factory of tree itself.

    Examples
    --------
    >>> from pcmdi_metrics.utils import tree
    >>> my_tree = tree()
    >>> my_tree['level1']['level2']['level3'] = 'value'
    >>> print(my_tree['level1']['level2']['level3'])  # Output: 'value'
    """
    return defaultdict(tree)
