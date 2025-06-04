from typing import Any, Optional, TypedDict


class ParsedKibanaURL(TypedDict):
    base_url: str
    _g: Optional[dict[str, Any]]
    _a: Optional[dict[str, Any]]
