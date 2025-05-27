from urllib.parse import urlparse, parse_qs, unquote
import json
import re
import prison

def decode_kibana_url(url: str, path: str) -> dict:
    parsed_url = urlparse(url)
    fragment = parsed_url.fragment.lstrip('?')  # remove the starting '?'

    # ✅ Use regex to extract _g and _a manually
    match_g = re.search(r"_g=([^&]+)", fragment)
    match_a = re.search(r"_a=([^&]+)", fragment)

    g_raw = unquote(match_g.group(1)) if match_g else ""
    a_raw = unquote(match_a.group(1)) if match_a else ""

    # Decode Rison using prison
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
        "base_url": url.split("#")[0],
        #"original_fragment": fragment,
        #"_g_raw": g_raw,
        #"_a_raw": a_raw,
        "_g": g_parsed,
        "_a": a_parsed
    }

    with open(path, "w") as file:
        json.dump(output, file, indent=2)

    print(f"✅ Saved decoded URL to {path}")
    return output
