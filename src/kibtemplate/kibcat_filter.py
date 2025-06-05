from enum import Enum, auto


class FilterOperators(Enum):

    IS = auto()
    IS_NOT = auto()
    IS_ONE_OF = auto()
    IS_NOT_ONE_OF = auto()
    EXISTS = auto()
    NOT_EXISTS = auto()


class KibCatFilter:
    field: str
    operator: FilterOperators
    value: str | list[str]

    def __init__(self, field: str, operator: FilterOperators, value: str | list[str]):
        self.field = field
        self.operator = operator
        self.value = value
