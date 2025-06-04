import re
from typing import Any

from elasticsearch import Elasticsearch


def extract_base_name(value: str) -> str:
    """Extracts the base value (The one that is always the same) given a field's value"""
    match = re.match(r"^([a-zA-Z0-9\-]+?)(?:-[a-z0-9]+.*)?$", value)
    return match.group(1) if match else value


def get_initial_part_of_fields(client: Elasticsearch, keyword_name: str) -> list[str]:
    """Get all the possible different initial values for the given field"""

    all_base_names: set[str] = set()
    after_key: Any = None

    while True:
        request_body: dict[str, Any] = {
            "size": 0,
            "aggs": {
                "result_values": {
                    "composite": {
                        "size": 10000,
                        "sources": [{"single_result": {"terms": {"field": keyword_name}}}],
                        **({"after": after_key} if after_key else {}),
                    }
                }
            },
        }

        response: Any = client.search(index=".ds-container-log-monthly-*", body=request_body)
        buckets: Any = response["aggregations"]["result_values"]["buckets"]

        for bucket in buckets:
            single_result: str = bucket["key"]["single_result"]
            base_name: str = extract_base_name(single_result)
            all_base_names.add(base_name)

        after_key = response["aggregations"]["result_values"].get("after_key")
        if not after_key:
            break

    return sorted(all_base_names)
