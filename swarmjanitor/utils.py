import dataclasses
import functools
import json
import operator
from enum import Enum
from typing import Any, List


class SmartEncoder(json.JSONEncoder):
    def default(self, o):
        if dataclasses.is_dataclass(o):
            return dataclasses.asdict(o)

        if isinstance(o, Enum):
            return o.value

        return super().default(o)


def flatten_list(list_of_lists: List[List[Any]]) -> List[Any]:
    return functools.reduce(operator.iconcat, list_of_lists, [])
