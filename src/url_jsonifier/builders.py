import json
from typing import Any, Optional, Type
from urllib.parse import quote

import prison

from ..kibcat_types.parsed_kibana_url import ParsedKibanaURL
from ..logging.base_logger import BaseKibCatLogger


def build_rison_url_from_json(
    path: Optional[str] = None,
    json_dict: Optional[ParsedKibanaURL] = None,
    LOGGER: Optional[Type[BaseKibCatLogger]] = None,
) -> str:
    """
    Reconstructs a Kibana URL by encoding `_g` and `_a` parameters as Rison and appending them
    to the base URL fragment. Input can be provided either via a JSON file or a dictionary.

    Args:
        path (Optional[str]): Path to a JSON file containing `base_url`, `_g`, and `_a`. Defaults to None.
        json_dict (Optional[Type[ParsedKibanaURL]]): Dictionary containing `base_url`, `_g`, and `_a`. Used if `path` is not provided.
        LOGGER (Optional[Type[BaseKibCatLogger]]): Logger for warnings or status messages.

    Returns:
        str: The reconstructed Kibana URL with Rison-encoded `_g` and `_a` parameters in the fragment.

    Raises:
        ValueError: If neither `path` nor `json_dict` is provided.
    """

    data: Optional[ParsedKibanaURL] = None

    # if path is passed read and load from file
    if path:
        try:
            with open(path, "r") as file:
                data = json.load(file)
        except Exception as e:
            msg = f"build_rison_url_from_json - Failed to load JSON from path.\n{e}"
            if LOGGER:
                LOGGER.error(msg)
            raise IOError(msg)

    # otherwise load from json_dict
    elif json_dict:
        data = json_dict

    # if data is None
    if not data:
        msg = f"build_rison_url_from_json - Neither data nor path provided."
        if LOGGER:
            LOGGER.error(msg)
        raise ValueError(msg)

    base_url: str | None = data.get("base_url")
    if not base_url:
        msg = "build_rison_url_from_json - 'base_url' is missing in the provided data."
        raise ValueError(msg)

    g_data: Optional[dict[str, Any]] = data.get("_g")
    a_data: Optional[dict[str, Any]] = data.get("_a")

    # Convert Python objects back to Rison strings, then URL encode them
    g_encoded: str = quote(prison.dumps(g_data)) if g_data else ""
    a_encoded: str = quote(prison.dumps(a_data)) if a_data else ""

    # Build the fragment string with _g and _a
    fragment_parts: list[str] = []
    if g_encoded:
        fragment_parts.append(f"_g={g_encoded}")
    if a_encoded:
        fragment_parts.append(f"_a={a_encoded}")

    fragment: str = "/?" + "&".join(fragment_parts) if fragment_parts else ""

    # Reconstruct the full URL with the fragment
    full_url = f"{base_url}#{fragment}"
    return full_url
