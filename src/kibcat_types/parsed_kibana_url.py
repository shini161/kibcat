from typing import TypedDict, Optional

class ParsedKibanaURL(TypedDict):
    base_url: str
    _g: Optional[dict]
    _a: Optional[dict]
