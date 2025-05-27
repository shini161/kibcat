from urllib.parse import urlparse, unquote, quote
from typing import Dict
import prison
import json
import re


def parse_rison_url_to_json(url: str, path: str | None = None) -> Dict:
    """
    Parses a Kibana URL containing Rison-encoded _g and _a parameters in the fragment,
    decodes and converts them to Python objects, and saves the result as JSON to a file.

    Args:
        url (str): The full Kibana URL to parse.
        path (str): The file path where the decoded JSON should be saved.

    Returns:
        dict: A dictionary with base_url, decoded _g, and decoded _a.
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
        print("⚠️ Failed to parse _g:", e)
        g_parsed = None

    try:
        a_parsed = prison.loads(a_raw) if a_raw else None
    except Exception as e:
        print("⚠️ Failed to parse _a:", e)
        a_parsed = None

    output = {
        "base_url": url.split("#")[0],  # URL before the fragment
        "_g": g_parsed,
        "_a": a_parsed
    }

    if path:
        with open(path, "w") as file:
            json.dump(output, file, indent=2)

        print(f"✅ Saved decoded URL to {path}")

    return output


def build_rison_url_from_json(path: str | None, json_dict: Dict | None = None) -> str:
    """
    Reads a JSON file with base_url, _g, and _a data,
    converts _g and _a back into Rison strings,
    and reconstructs the full Kibana URL with Rison-encoded fragment.

    Args:
        path (str): Path to the JSON file containing base_url, _g, and _a.

    Returns:
        str: The reconstructed Kibana URL with Rison-encoded _g and _a in the fragment.
    """

    data = None

    if path:
        with open(path, "r") as file:
            data = json.load(file)
    else:
        data = json_dict

    if not data:
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
