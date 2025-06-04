from elasticsearch import Elasticsearch
from typing import Any
import re

from elasticsearch import Elasticsearch


def extract_base_name(value: str) -> str:
    """Extracts the base value (The one that is always the same) given a field's value"""
    match = re.match(r"^([a-zA-Z0-9\-]+?)(?:-[a-z0-9]+.*)?$", value)
    return match.group(1) if match else value


from collections import defaultdict
from typing import List, Dict, Union


def recursive_group(
    elements: set[str] | List[str], level: int = 0
) -> Union[List[str], Dict[str, Union[Dict, List[str]]]] | set[str]:
    if not elements:
        return []

    grouped = defaultdict(list)

    for element in elements:
        parts = element.split("-")
        if len(parts) > level:
            key = parts[level]
            grouped[key].append(element)
        else:
            # Reached the end of this element — put under a special key
            grouped["_end"].append(element)
            
    if all(len(v) == 1 for v in grouped.values()):
        return elements

    result = {}
    for key, group_elements in grouped.items():
        # Check if all items are the same or cannot be split further
        unique_remainders = set(e for e in group_elements)
        if len(unique_remainders) == 1 or all(
            len(e.split("-")) <= level + 1 for e in group_elements
        ):
            result[key] = group_elements
        else:
            result[key] = recursive_group(group_elements, level + 1)

    return result


def get_initial_part_of_fields(client: Elasticsearch, keyword_name: str) -> list[str]:
    """Get all the possible different initial values for the given field.
    It is different from the suggested values since this one gets the values the field actually has.
    """


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
            # base_name: str = extract_base_name(single_result)
            # all_base_names.add(base_name)
            all_field_names.add(single_result)

        after_key = response["aggregations"]["result_values"].get("after_key")
        if not after_key:
            break

    # values_dict = {}

    # for element in all_field_names:
    #     element_splitted = element.split("-")

    #     if not element_splitted:
    #         continue

    #     base_name = element_splitted[0]
    #     if base_name not in values_dict:
    #         values_dict[base_name] = [element]
    #     else:
    #         values_dict[base_name].append(element)

    # for first_part, elements in values_dict.items():

    #     for element in elements:
    #         element_splitted = element.split("-")

    grouped = recursive_group(all_field_names)
    from pprint import pprint

    pprint(grouped, width=120)

    # return sorted(all_field_names)
    return []
