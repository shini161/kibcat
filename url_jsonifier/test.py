from encoder import encode_kibana_url
from decoder import decode_kibana_url
import os
import json

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FOLDER = os.path.join(BASE_DIR, "data")
URL_DECODE_PATH = os.path.join(DATA_FOLDER, "decode.json")

os.makedirs(DATA_FOLDER, exist_ok=True) # Creates dir "data" if it doesnt exist

KIBANA_URL = "https://kibana-logging-devops-pcto.stella.cloud.az.cgm.ag/app/discover#/?_g=(filters:!(),refreshInterval:(pause:!t,value:60000),time:(from:'2025-05-09T18:02:40.258Z',to:'2025-05-10T02:05:46.064Z'))&_a=(columns:!(agent.id,cometa.log.message,kubernetes.namespace,kubernetes.pod.name),dataSource:(dataViewId:'container-log*',type:dataView),filters:!(),grid:(columns:('@timestamp':(width:127),agent.id:(width:159),cometa.log.message:(width:249),kubernetes.namespace:(width:202))),interval:auto,query:(language:kuery,query:'kubernetes.pod.name%20:%20%22backend%22'),sort:!(!('@timestamp',desc)))"


# Decode URL
print("\033[91m---- DECODE URL ----\033[0m")
url_to_json = decode_kibana_url(KIBANA_URL, URL_DECODE_PATH)
print(json.dumps(url_to_json, indent=2))


# Encode URL
print("\033[91m---- ENCODE URL ----\033[0m")
json_to_url = encode_kibana_url(URL_DECODE_PATH)
print(f"{json_to_url}")
