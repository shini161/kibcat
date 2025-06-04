"""Type definitions related to parsed Kibana URLs."""

from typing import Any, Optional, TypedDict


class ParsedKibanaURL(TypedDict):
    """TypedDict describing the structure of a parsed Kibana URL."""

    base_url: str
    _g: Optional[dict[str, Any]]
    _a: Optional[dict[str, Any]]
