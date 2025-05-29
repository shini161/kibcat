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


