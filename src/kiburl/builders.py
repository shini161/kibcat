import json
from typing import Any, Type
from urllib.parse import quote

import prison

from kiblog import BaseLogger
from kibtypes import ParsedKibanaURL


def build_rison_url_from_json(
    path: str | None = None,
    json_dict: ParsedKibanaURL | None = None,
    logger: Type[BaseLogger] | None = None,
) -> str:
    """
    Reconstructs a Kibana URL by encoding `_g` and `_a` parameters as Rison and appending them
    to the base URL fragment. Input can be provided either via a JSON file or a dictionary.

    Args:
        path (str | None): Path to a JSON file containing `base_url`, `_g`, and `_a`. Defaults to None.
        json_dict (Type[ParsedKibanaURL] | None): Dictionary containing `base_url`, `_g`, and `_a`.
        Used if `path` is not provided.
        logger (Type[BaseLogger] | None): Logger for warnings or status messages.

    Returns:
        str: The reconstructed Kibana URL with Rison-encoded `_g` and `_a` parameters in the fragment.

    Raises:
        ValueError: If neither `path` nor `json_dict` is provided.
    """

    data: ParsedKibanaURL | None = None

    # if path is passed read and load from file
    if path:
        try:
            with open(path, "r", encoding="utf-8") as file:
                data = json.load(file)
        except Exception as e:
            msg = f"[kiburl.build_rison_url_from_json] - Failed to load JSON from path.\n{e}"
            if logger:
                logger.error(msg)
            raise IOError(msg) from e

    # otherwise load from json_dict
    elif json_dict:
        data = json_dict

    # if data is None
    if not data:
        msg = "[kiburl.build_rison_url_from_json] - Neither data nor path provided."
        if logger:
            logger.error(msg)
        raise ValueError(msg)

    base_url: str | None = data.get("base_url")
    if not base_url:
        msg = "[kiburl.build_rison_url_from_json] - 'base_url' is missing in the provided data."
        raise ValueError(msg)

    g_data: dict[str, Any] | None = data.get("_g")
    a_data: dict[str, Any] | None = data.get("_a")

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
