# Currently, while testing, the example part of this module will be there. Once done it will be moved to the examples folder.

from elasticsearch import Elasticsearch
from dotenv import load_dotenv
import re
import os

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


es = Elasticsearch(BASE_URL, http_auth=(USERNAME, PASS), verify_certs=False)

# Query elastic
response = es.search(
    index=DATA_VIEW_ID,
    size=0,
    aggs={"pod_names": {"terms": {"field": "kubernetes.pod.name", "size": 10000}}},
)


def extract_base_name(pod_name):
    match = re.match(r"^([a-zA-Z0-9\-]+?)(?:-[0-9a-z]+.*)?$", pod_name)
    return match.group(1) if match else pod_name


pod_names = [bucket["key"] for bucket in response["aggregations"]["pod_names"]["buckets"]]
base_names = sorted(set(extract_base_name(name) for name in pod_names))

# Output
print(base_names)
