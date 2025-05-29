from utils import parse_rison_url_to_json, build_rison_url_from_json
import os
import json

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FOLDER = os.path.join(BASE_DIR, "data")
URL_DECODE_PATH = os.path.join(DATA_FOLDER, "decode.json")

# Creates dir "data" if it doesnt exist
os.makedirs(DATA_FOLDER, exist_ok=True)

KIBANA_URL = "https://kibana-logging-devops-pcto.stella.cloud.az.cgm.ag/app/discover#/?_g=(filters:!(),refreshInterval:(pause:!t,value:60000),time:(from:'2025-05-09T18:02:40.258Z',to:'2025-05-10T02:05:46.064Z'))&_a=(columns:!(agent.id,cometa.log.message,kubernetes.namespace,kubernetes.pod.name),dataSource:(dataViewId:'container-log*',type:dataView),filters:!(('$state':(store:appState),meta:(alias:!n,disabled:!f,field:kubernetes.namespace,index:'container-log*',key:kubernetes.namespace,negate:!f,params:(query:qa),type:phrase),query:(match_phrase:(kubernetes.namespace:qa)))),grid:(columns:('@timestamp':(width:127),agent.id:(width:159),cometa.log.message:(width:249),kubernetes.namespace:(width:202))),interval:auto,query:(language:kuery,query:'kubernetes.pod.name%20:%20%22backend%22'),sort:!(!('@timestamp',desc)))"

COLOR_RED = "\033[91m"
COLOR_RESET = "\033[0m"

# Parse Kibana URL to JSON
print(f"{COLOR_RED}---- PARSE URL ----{COLOR_RESET}")
url_to_json = parse_rison_url_to_json(KIBANA_URL, URL_DECODE_PATH)
print(json.dumps(url_to_json, indent=2))


# Rebuild Kibana URL from JSON
print(f"{COLOR_RED}---- BUILD URL ----{COLOR_RESET}")
json_to_url = build_rison_url_from_json(URL_DECODE_PATH)
print(f"{json_to_url}")
