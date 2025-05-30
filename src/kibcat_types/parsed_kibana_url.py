from typing import TypedDict, Optional, Any


class ParsedKibanaURL(TypedDict):
    base_url: str
    _g: Optional[dict[str, Any]]
    _a: Optional[dict[str, Any]]
