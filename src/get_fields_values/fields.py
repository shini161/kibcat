# Currently, while testing, the example part of this module will be there. Once done it will be moved to the examples folder.

from elasticsearch import Elasticsearch
from dotenv import load_dotenv
import re
import os
from elastic_transport import NodeConfig
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

load_dotenv()

BASE_URL = os.getenv("ELASTIC_URL")
USERNAME = os.getenv("KIBANA_USERNAME")
PASS = os.getenv("KIBANA_PASS")
DATA_VIEW_ID = os.getenv("KIBANA_DATA_VIEW_ID")


if not BASE_URL or not USERNAME or not PASS:
    msg = "One of the fields is missing."

    print(msg)
    exit(1)


print(f"Connecting to elastic at: {BASE_URL}")


node_config = NodeConfig(
    scheme="https",
    host=BASE_URL.split("://")[-1].split(":")[0],
    port=443,
    verify_certs=False,
)

es = Elasticsearch([node_config], basic_auth=(USERNAME, PASS))

print(es.info())


def extract_base_name(pod_name):
    match = re.match(r"^([a-zA-Z0-9\-]+?)(?:-[a-z0-9]+.*)?$", pod_name)
    return match.group(1) if match else pod_name


all_base_names = set()
after_key = None

while True:
    body = {
        "size": 0,
        "aggs": {
            "pod_names": {
                "composite": {
                    "size": 1000,
                    "sources": [{"pod_name": {"terms": {"field": "kubernetes.pod.name.keyword"}}}],
                    **({"after": after_key} if after_key else {}),
                }
            }
        },
    }

    response = es.search(index=".ds-container-log-monthly-*", body=body)
    buckets = response["aggregations"]["pod_names"]["buckets"]

    for bucket in buckets:
        pod_name = bucket["key"]["pod_name"]
        base_name = extract_base_name(pod_name)
        all_base_names.add(base_name)

    after_key = response["aggregations"]["pod_names"].get("after_key")
    if not after_key:
        break

print(sorted(all_base_names))
