import os
import json
from helper import decode_kibana_url, encode_kibana_url


ENCODE_URL = True # Change this to encode or decode the url here
KIBANA_URL = "https://kibana-logging-devops-pcto.stella.cloud.az.cgm.ag/app/discover#/?_g=(filters:!(),refreshInterval:(pause:!t,value:60000),time:(from:'2025-05-09T08:41:12.862Z',to:'2025-05-10T10:20:52.276Z'))&_a=(columns:!(agent.id,cometa.log.message,kubernetes.namespace,kubernetes.pod.name),dataSource:(dataViewId:'container-log*',type:dataView),filters:!(),grid:(columns:('@timestamp':(width:127),agent.id:(width:159),cometa.log.message:(width:249),kubernetes.namespace:(width:202))),interval:auto,query:(language:kuery,query:'kubernetes.pod.name%20:%20%22backend%22'),sort:!(!('@timestamp',desc)))"


if __name__ == "__main__":
    folder_path = os.path.join(os.path.dirname(__file__), "parts")

    if not os.path.exists(folder_path):
        os.mkdir(folder_path)

    base_url_path = os.path.join(folder_path, "baseurl.json")
    g_part_path = os.path.join(folder_path, "g_part.json")
    a_part_path = os.path.join(folder_path, "a_part.json")

    if ENCODE_URL:
        with open(base_url_path, "r") as f:
            base_url = json.load(f)["URL"]
        with open(g_part_path, "r") as f:
            g_obj = json.load(f)
        with open(a_part_path, "r") as f:
            a_obj = json.load(f)

        encoded_url = encode_kibana_url(base_url, g_obj, a_obj)

        print(f"Encoded Kibana URL: {encoded_url}")

    else:
        base_url, g_part, a_part = decode_kibana_url(KIBANA_URL)

        print(f"Base URL: {base_url}")

        with open(base_url_path, "w") as f:
            json.dump({"URL": base_url}, f, indent=2)
        with open(g_part_path, "w") as f:
            json.dump(g_part, f, indent=2)
        with open(a_part_path, "w") as f:
            json.dump(a_part, f, indent=2)

        print(f"Parts saved to {folder_path}")
