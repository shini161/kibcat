from urllib.parse import quote
from typing import Dict
import prison
import json


def build_rison_url_from_json(path: str | None = None, json_dict: Dict | None = None, LOGGER=None) -> str:
    """
    Reconstructs a Kibana URL with Rison-encoded _g and _a fragments from a JSON file or dictionary.

    Args:
        path (str, optional): Path to the JSON file containing base_url, _g, and _a. Defaults to None.
        json_dict (Dict, optional): Dictionary with base_url, _g, and _a. Used if path is not provided.

    Returns:
        str: reconstructed Kibana URL with Rison-encoded _g and _a in the fragment.

    Raises:
        ValueError: If neither path nor json_dict is provided
    """

    data: Dict | None = None

    # if path is passed read and load from file
    if path:
        with open(path, "r") as file:
            data = json.load(file)
    # otherwise load from json_dict
    else:
        data = json_dict

    # if data is None
    if not data:
        if LOGGER:
            LOGGER.error("build_rison_url_from_json - Nor data nor path found")
        raise ValueError("Nor data nor path found")

    base_url: str = data.get("base_url")
    g_data: Dict | None = data.get("_g")
    a_data: Dict | None = data.get("_a")

    # Convert Python objects back to Rison strings, then URL encode them
    g_encoded: str = quote(prison.dumps(g_data)) if g_data else ""
    a_encoded: str = quote(prison.dumps(a_data)) if a_data else ""

    # Build the fragment string with _g and _a
    fragment_parts: list[str] = []
    if g_encoded:
        fragment_parts.append(f"_g={g_encoded}")
    if a_encoded:
        fragment_parts.append(f"_a={a_encoded}")
    fragment = "/?" + "&".join(fragment_parts)

    # Reconstruct the full URL with the fragment
    full_url = f"{base_url}#{fragment}"
    return full_url
