import dataclasses
import functools
import json
import operator
from enum import Enum
from typing import List, TypeVar


class SmartEncoder(json.JSONEncoder):
    def default(self, o):
        if dataclasses.is_dataclass(o):
            return dataclasses.asdict(o)

        if isinstance(o, Enum):
            return o.value

        return super().default(o)


T = TypeVar('T')


def flatten_list(list_of_lists: List[List[T]]) -> List[T]:
    return functools.reduce(operator.iconcat, list_of_lists, [])
