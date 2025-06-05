import os
from typing import Type

import urllib3
from dotenv import load_dotenv
from elastic_transport import NodeConfig
from elasticsearch import Elasticsearch

from kibfieldvalues import get_initial_part_of_fields
from kiblog import BaseLogger

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

load_dotenv()


def run_example(
    base_url: str, username: str, password: str, data_view_id: str, logger: Type[BaseLogger] | None = None
) -> None:
    """Connect to Elasticsearch and log initial values of a specific field."""

    if logger:
        logger.message(f"[examples.kibfieldvalues] - Connecting to elastic at: {base_url}")

    node_config: NodeConfig = NodeConfig(
        scheme="https",
        host=base_url.split("://")[-1].split(":")[0],
        port=443,
        verify_certs=False,
    )

    es: Elasticsearch = Elasticsearch([node_config], basic_auth=(username, password))

    if logger:
        logger.message(f"[examples.kibfieldvalues] - {es.info()}\n")

    # This is just an example, it can be changed when using this file
    example_field = "kubernetes.pod.name.keyword"

    if logger:
        logger.message(f"{get_initial_part_of_fields(es, example_field, data_view_id)}")


if __name__ == "__main__":
    BASE_URL: str | None = os.getenv("ELASTIC_URL")
    USERNAME: str | None = os.getenv("KIBANA_USERNAME")
    PASS: str | None = os.getenv("KIBANA_PASS")
    DATA_VIEW_ID: str | None = os.getenv("KIBANA_DATA_VIEW_ID")

    if not BASE_URL or not USERNAME or not PASS or not DATA_VIEW_ID:
        msg = "[examples.kibfieldvalues] - One of the fields is missing."  # pylint: disable=invalid-name
        BaseLogger.error(msg)
        raise RuntimeError(msg)

    run_example(base_url=BASE_URL, username=USERNAME, password=PASS, data_view_id=DATA_VIEW_ID, logger=BaseLogger)
