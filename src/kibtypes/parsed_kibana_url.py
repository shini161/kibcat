from typing import Any, TypedDict


class ParsedKibanaURL(TypedDict):
    """TypedDict describing the structure of a parsed Kibana URL."""

    base_url: str
    _g: dict[str, Any] | None
    _a: dict[str, Any] | None
