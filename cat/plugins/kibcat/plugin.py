from cat.mad_hatter.decorators import tool
from cat.plugins.kibcat.imports.url_jsonifier.builders import build_rison_url_from_json
from cat.plugins.kibcat.imports.url_jsonifier.parsers import parse_rison_url_to_json
import json

@tool
def socks_prices(color, cat):
    """How much do socks cost? Input is the sock color."""
    prices = {
        "black": 5,
        "white": 10,
        "pink": 50,
    }
    KIBANA_URL = (
        "https://localhost:9200/app/discover#/?_g="
        "(filters:!(),refreshInterval:(pause:!t,value:60000),"
        "time:(from:'2025-05-09T18:02:40.258Z',to:'2025-05-10T02:05:46.064Z'))&_a="
        "(columns:!(choco.id,log.message,example.namespace,example.name),"
        "dataSource:(dataViewId:'logs*',type:dataView),"
        "filters:!(('$state':(store:appState),"
        "meta:(alias:!n,disabled:!f,field:example.namespace,index:'logs*',"
        "key:example.namespace,negate:!f,params:(query:qa),type:phrase),"
        "query:(match_phrase:(example.namespace:qa)))),"
        "grid:(columns:('@timestamp':(width:127),choco.id:(width:159),"
        "log.message:(width:249),example.namespace:(width:202))),"
        "interval:auto,query:(language:kuery,query:'example.name%20:%20%22backend%22'),"
        "sort:!(!('@timestamp',desc)))"
        )

    COLOR_RED = "\033[91m"
    COLOR_RESET = "\033[0m"

        # Parse Kibana URL to JSON
    print(f"{COLOR_RED}---- PARSE URL ----{COLOR_RESET}")
    json_url = parse_rison_url_to_json(KIBANA_URL)
    print(json.dumps(json_url, indent=2))


        # Rebuild Kibana URL from JSON from file
    print(f"{COLOR_RED}---- BUILD URL FROM FILE ----{COLOR_RESET}")
    rison_url_from_json = build_rison_url_from_json(None, json_url)
    print(f"{rison_url_from_json}")

#
    if color not in prices.keys():
        return f"No {color} socks"
    else:
        return f"{prices[color]} €"
