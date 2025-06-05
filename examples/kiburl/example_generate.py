import json
import os

from kiblog import BaseLogger
from kiburl import build_rison_url_from_json, parse_rison_url_to_json

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

# Parse Kibana URL to JSON
BaseLogger.message("[example.kiburl] - PARSE URL")
JSON_URL = parse_rison_url_to_json(url=KIBANA_URL, path=OUTPUT_FILE_PATH, logger=BaseLogger)
BaseLogger.message(json.dumps(JSON_URL, indent=2))


# Rebuild Kibana URL from JSON from file
BaseLogger.message("[example.kiburl] - BUILD URL FROM FILE")
RISON_URL_FROM_FILE = build_rison_url_from_json(path=OUTPUT_FILE_PATH, logger=BaseLogger)
BaseLogger.message(f"{RISON_URL_FROM_FILE}")

# Rebuild Kibana URL from JSON from json
BaseLogger.message("[example.kiburl] - BUILD URL FROM JSON")
RISON_URL_FROM_JSON = build_rison_url_from_json(json_dict=JSON_URL, logger=BaseLogger)
BaseLogger.message("f{RISON_URL_FROM_JSON}")
