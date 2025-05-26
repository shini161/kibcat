from typing import Tuple
import prison
import urllib.parse
from urllib.parse import urlparse


def decode_kibana_url(url) -> Tuple[str, str, str]:
    """Decodes the given Kibana URL into its JSON components.

    Returns:
        Tuple[ base url , json_g , json_a ]"""

    parsed = urlparse(url)
    fragment = parsed.fragment

    base_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
    query_parts = urllib.parse.parse_qs(fragment)

    g_encoded = query_parts.get('_g', [None])[0]
    a_encoded = query_parts.get('_a', [None])[0]

    try:
        g_decoded = prison.loads(urllib.parse.unquote(
            g_encoded)) if g_encoded else {}
        a_decoded = prison.loads(urllib.parse.unquote(
            a_encoded)) if a_encoded else {}
    except Exception as e:
        print("Error decoding Rison:", e)
        return

    return (base_url, g_decoded, a_decoded)


def encode_kibana_url(base_url, g_part, a_part):
    """Encodes the given parameters in a Kibana URL"""

    g_encoded = urllib.parse.quote(prison.dumps(g_part))
    a_encoded = urllib.parse.quote(prison.dumps(a_part))

    final_url = f"{base_url}#/?_g={g_encoded}&_a={a_encoded}"
    return final_url
