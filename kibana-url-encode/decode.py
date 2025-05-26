import json
import prison
import urllib.parse
from urllib.parse import urlparse


def decode_kibana_url(url, output_prefix="kibana_state"):
    parsed = urlparse(url)
    fragment = parsed.fragment

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

    with open(f"{output_prefix}_g.json", "w") as f:
        json.dump(g_decoded, f, indent=2)
    with open(f"{output_prefix}_a.json", "w") as f:
        json.dump(a_decoded, f, indent=2)

    print(
        f"saved to '{output_prefix}_g.json' and '{output_prefix}_a.json'")


kibana_url = "https://***REMOVED***/app/discover#/?_g=(filters:!(),refreshInterval:(pause:!t,value:60000),time:(from:'2025-05-09T08:41:12.862Z',to:'2025-05-10T10:20:52.276Z'))&_a=(columns:!(agent.id,***REMOVED***,***REMOVED***,***REMOVED***),dataSource:(dataViewId:'container-log*',type:dataView),filters:!(),grid:(columns:('@timestamp':(width:127),agent.id:(width:159),***REMOVED***:(width:249),***REMOVED***:(width:202))),interval:auto,query:(language:kuery,query:'***REMOVED***%20:%20%22backend%22'),sort:!(!('@timestamp',desc)))"

decode_kibana_url(kibana_url, output_prefix="url")
