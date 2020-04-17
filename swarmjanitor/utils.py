import functools
import operator
from typing import Any, List


def flatten_list(list_of_lists: List[List[Any]]) -> List[Any]:
    return functools.reduce(operator.iconcat, list_of_lists, [])
