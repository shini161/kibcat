import json
from urllib.parse import quote
import prison

def encode_kibana_url(path: str) -> str:
    with open(path, "r") as file:
        data = json.load(file)

    base_url = data.get("base_url", "")
    g_data = data.get("_g")
    a_data = data.get("_a")

    # Encode dicts to Rison and URL-safe strings
    g_encoded = quote(prison.dumps(g_data)) if g_data else ""
    a_encoded = quote(prison.dumps(a_data)) if a_data else ""

    # Build URL fragment
    fragment_parts = []
    if g_encoded:
        fragment_parts.append(f"_g={g_encoded}")
    if a_encoded:
        fragment_parts.append(f"_a={a_encoded}")
    fragment = "/?" + "&".join(fragment_parts)

    # Combine base URL and fragment
    full_url = f"{base_url}#{fragment}"
    return full_url

