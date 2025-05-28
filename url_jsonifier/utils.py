from urllib.parse import urlparse, unquote, quote
from typing import Dict
import prison
import json
import re


def parse_rison_url_to_json(url: str, path: str | None = None, LOGGER=None) -> Dict:
    """
    Parses a Kibana URL containing Rison-encoded `_g` and `_a` parameters in the fragment,
    decodes them into Python dictionaries, and optionally saves the result to a JSON file.

    Args:
        url (str): The full Kibana URL to parse.
        path (str, optional): If provided, the decoded data will be saved to this file path as JSON.

    Returns:
        dict: A dictionary with the following keys:
            - base_url (str): The part of the URL before the fragment.
            - _g (dict or None): Decoded `_g` parameter, or None if not present or failed to decode.
            - _a (dict or None): Decoded `_a` parameter, or None if not present or failed to decode.
    """

    parsed_url = urlparse(url)
    # Extract the fragment part and strip leading '?' if present
    fragment = parsed_url.fragment.lstrip("?")

    # Use regex to find the _g and _a Rison parts in the fragment
    match_g = re.search(r"_g=([^&]+)", fragment)
    match_a = re.search(r"_a=([^&]+)", fragment)

    # URL decode the matched Rison strings
    g_raw = unquote(match_g.group(1)) if match_g else ""
    a_raw = unquote(match_a.group(1)) if match_a else ""

    # Parse the Rison strings into Python objects
    try:
        g_parsed = prison.loads(g_raw) if g_raw else None
    except Exception as e:
        if LOGGER:
            LOGGER.warning(f"⚠️ Failed to parse _g: {e}")
        g_parsed = None

    try:
        a_parsed = prison.loads(a_raw) if a_raw else None
    except Exception as e:
        if LOGGER:
            LOGGER.warning(f"⚠️ Failed to parse _a: {e}")
        a_parsed = None

    output = {
        "base_url": url.split("#")[0],  # URL before the fragment
        "_g": g_parsed,
        "_a": a_parsed
    }

    # if path is passed, save to path
    if path:
        with open(path, "w") as file:
            json.dump(output, file, indent=2)

        if LOGGER:
            LOGGER.message(f"✅ Saved decoded URL to {path}")

    return output


def build_rison_url_from_json(path: str | None = None, json_dict: Dict | None = None, LOGGER=None) -> str:
    """
    Reconstructs a Kibana URL with Rison-encoded _g and _a fragments from a JSON file or dictionary.

    Args:
        path (str, optional): Path to the JSON file containing base_url, _g, and _a. Defaults to None.
        json_dict (Dict, optional): Dictionary with base_url, _g, and _a. Used if path is not provided.

    Returns:
        str: The reconstructed Kibana URL with Rison-encoded _g and _a in the fragment.

    Raises:
        ValueError: If neither path nor json_dict is provided or if they contain invalid data.
    """

    data = None

    # if path is passed read and load from file
    if path:
        with open(path, "r") as file:
            data = json.load(file)
    # otherwise load from json_dict
    else:
        data = json_dict

    if not data:
        if LOGGER:
            LOGGER.error("build_rison_url_from_json - Nor data nor path found")
        raise ValueError("Nor data nor path found")

    base_url = data.get("base_url")
    g_data = data.get("_g")
    a_data = data.get("_a")

    # Convert Python objects back to Rison strings, then URL encode them
    g_encoded = quote(prison.dumps(g_data)) if g_data else ""
    a_encoded = quote(prison.dumps(a_data)) if a_data else ""

    # Build the fragment string with _g and _a
    fragment_parts = []
    if g_encoded:
        fragment_parts.append(f"_g={g_encoded}")
    if a_encoded:
        fragment_parts.append(f"_a={a_encoded}")
    fragment = "/?" + "&".join(fragment_parts)

    # Reconstruct the full URL with the fragment
    full_url = f"{base_url}#{fragment}"
    return full_url
