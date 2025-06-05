from enum import Enum, auto


class FilterOperators(Enum):
    """Enumeration of filter operators used in KibCat filtering."""

    IS = auto()
    IS_NOT = auto()
    IS_ONE_OF = auto()
    IS_NOT_ONE_OF = auto()
    EXISTS = auto()
    NOT_EXISTS = auto()


class KibCatFilter:
    """
    Represents a filter condition for querying data.

    Attributes:
        field (str): The name of the field to filter on.
        operator (FilterOperators): The filter operation to apply.
        value (str | list[str]): The value(s) used for filtering.
    """

    field: str
    operator: FilterOperators
    value: str | list[str]

    def __init__(self, field: str, operator: FilterOperators, value: str | list[str]):
        self.field = field
        self.operator = operator
        self.value = value
