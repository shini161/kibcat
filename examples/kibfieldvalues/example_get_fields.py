from elasticsearch import Elasticsearch
from dotenv import load_dotenv
from elastic_transport import NodeConfig
from kibfieldvalues import get_initial_part_of_fields
import os
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

load_dotenv()

BASE_URL: str | None = os.getenv("ELASTIC_URL")
USERNAME: str | None = os.getenv("KIBANA_USERNAME")
PASS: str | None = os.getenv("KIBANA_PASS")
DATA_VIEW_ID: str | None = os.getenv("KIBANA_DATA_VIEW_ID")


if not BASE_URL or not USERNAME or not PASS or not DATA_VIEW_ID:
    msg = "One of the fields is missing."

    print(msg)
    exit(1)

print(f"Connecting to elastic at: {BASE_URL}")

node_config: NodeConfig = NodeConfig(
    scheme="https",
    host=BASE_URL.split("://")[-1].split(":")[0],
    port=443,
    verify_certs=False,
)

es: Elasticsearch = Elasticsearch([node_config], basic_auth=(USERNAME, PASS))

print(es.info())
print()

# This is just an example, it can be changed when using this file
EXAMPLE_FIELD = "kubernetes.pod.name.keyword"

print(get_initial_part_of_fields(es, EXAMPLE_FIELD))
