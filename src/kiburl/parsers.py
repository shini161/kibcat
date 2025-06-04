import json
import re
from typing import Any, Optional, Type
from urllib.parse import unquote, urlparse

import prison

from kiblog import BaseLogger
from kibtypes import ParsedKibanaURL


def parse_rison_url_to_json(
    url: str, path: Optional[str] = None, LOGGER: Optional[Type[BaseLogger]] = None
) -> ParsedKibanaURL:
    """
    Parses a Kibana URL containing Rison-encoded `_g` and `_a` parameters in the fragment,
    decodes them into Python dictionaries, and optionally writes the output to a JSON file.

    Args:
        url (str): The full Kibana URL to parse.
        path (Optional[str]): If provided, the decoded result will be saved to this file as JSON.
        LOGGER (Optional[Type[BaseKibCatLogger]]): Logger for warnings or messages.

    Returns:
        ParsedKibanaURL: Dictionary with keys:
            - 'base_url': The portion of the URL before the fragment.
            - '_g': Decoded `_g` object (or None if missing or invalid).
            - '_a': Decoded `_a` object (or None if missing or invalid).
    """

    parsed_url = urlparse(url)
    # Extract the fragment part and strip leading '?' if present
    fragment: str = parsed_url.fragment.lstrip("?")

    # Use regex to find the _g and _a Rison parts in the fragment
    match_g = re.search(r"_g=([^&]+)", fragment)
    match_a = re.search(r"_a=([^&]+)", fragment)

    # URL decode the matched Rison strings
    g_raw: str = unquote(match_g.group(1)) if match_g else ""
    a_raw: str = unquote(match_a.group(1)) if match_a else ""

    g_parsed: Optional[dict[str, Any]] = None
    a_parsed: Optional[dict[str, Any]] = None

    # Parse the Rison strings into Python objects
    try:
        g_parsed = prison.loads(g_raw) if g_raw else None
    except Exception as e:
        msg = f"parse_rison_url_to_json - Failed to parse _g.\n{e}"
        if LOGGER:
            LOGGER.warning(msg)

    try:
        a_parsed = prison.loads(a_raw) if a_raw else None
    except Exception as e:
        msg = f"parse_rison_url_to_json - Failed to parse _a.\n{e}"
        if LOGGER:
            LOGGER.warning(msg)

    result: ParsedKibanaURL = {
        "base_url": url.split("#")[0],  # URL before the fragment
        "_g": g_parsed,
        "_a": a_parsed,
    }

    # if path is passed, save to path
    if path:
        try:
            with open(path, "w") as file:
                json.dump(result, file, indent=2)

            msg = f"parse_rison_url_to_json - Saved decoded URL to {path}"
            if LOGGER:
                LOGGER.message(msg)
        except Exception as e:
            msg = f"parse_rison_url_to_json - Failed to save JSON to {path}.\n{e}"
            if LOGGER:
                LOGGER.error(msg)
            raise Exception(msg)

    return result
