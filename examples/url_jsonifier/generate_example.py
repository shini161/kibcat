from src.url_jsonifier.builders import build_rison_url_from_json
from src.url_jsonifier.parsers import parse_rison_url_to_json
import json
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FOLDER = os.path.join(BASE_DIR, "data")
OUTPUT_FILE_PATH = os.path.join(DATA_FOLDER, "parsed_rison.json")

# Creates dir "data" if it doesnt exist
os.makedirs(DATA_FOLDER, exist_ok=True)

KIBANA_URL = (
        "https://localhost:9200/app/discover#/?_g="
        "(filters:!(),refreshInterval:(pause:!t,value:60000),"
        "time:(from:'2025-05-09T18:02:40.258Z',to:'2025-05-10T02:05:46.064Z'))&_a="
        "(columns:!(example.id,log.message,example.namespace,example.name),"
        "dataSource:(dataViewId:'logs*',type:dataView),"
        "filters:!(('$state':(store:appState),"
        "meta:(alias:!n,disabled:!f,field:example.namespace,index:'logs*',"
        "key:example.namespace,negate:!f,params:(query:qa),type:phrase),"
        "query:(match_phrase:(example.namespace:qa)))),"
        "grid:(columns:('@timestamp':(width:127),example.id:(width:159),"
        "log.message:(width:249),example.namespace:(width:202))),"
        "interval:auto,query:(language:kuery,query:'example.name%20:%20%22backend%22'),"
        "sort:!(!('@timestamp',desc)))"
        )

COLOR_RED = "\033[91m"
COLOR_RESET = "\033[0m"

# Parse Kibana URL to JSON
print(f"{COLOR_RED}---- PARSE URL ----{COLOR_RESET}")
json_url = parse_rison_url_to_json(KIBANA_URL, OUTPUT_FILE_PATH)
print(json.dumps(json_url, indent=2))


# Rebuild Kibana URL from JSON from file
print(f"{COLOR_RED}---- BUILD URL FROM FILE ----{COLOR_RESET}")
rison_url_from_file = build_rison_url_from_json(OUTPUT_FILE_PATH)
print(f"{rison_url_from_file}")

# Rebuild Kibana URL from JSON from json
print(f"{COLOR_RED}---- BUILD URL FROM JSON ----{COLOR_RESET}")
rison_url_from_json = build_rison_url_from_json(None, json_url)
print("f{rison_url_from_json}")
