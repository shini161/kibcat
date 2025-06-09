from enum import Enum, auto
from typing import Any, Union

from pydantic import BaseModel, field_serializer


class FilterOperators(Enum):
    """Enumeration of filter operators used in KibCat filtering."""

    IS = auto()
    IS_NOT = auto()
    IS_ONE_OF = auto()
    IS_NOT_ONE_OF = auto()
    EXISTS = auto()
    NOT_EXISTS = auto()


class KibCatFilter(BaseModel):
    """
    Represents a filter condition for querying data.

    Attributes:
        field (str): The name of the field to filter on.
        operator (FilterOperators): The filter operation to apply.
        value (str | list[str]): The value(s) used for filtering.
    """

    field: str
    operator: FilterOperators
    value: Union[str, List[str], None]

    def __init__(self, field: str, operator: FilterOperators, value: Union[str, list[str]], **kwargs: Any) -> None:
        super().__init__(field=field, operator=operator, value=value, **kwargs)

    @field_serializer("operator")
    def serialize_operator(self, operator: FilterOperators) -> str:
        """
        Serializes the FilterOperators enum to its name as a string.

        Args:
            operator (FilterOperators): The operator to serialize.

        Returns:
            str: The string name of the operator.
        """
        return operator.name
