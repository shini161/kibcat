from collections import defaultdict
from enum import Enum, auto
from typing import Any, Optional, TypeAlias

from elasticsearch import Elasticsearch


class FieldsTag(Enum):
    """
    Enum to indicate the end of a branch in the recursive fields dictionary.

    Attributes:
        END: Marks the end of a branch in the field structure.
    """

    END = auto()


# Typing for the recursive function
FieldGroupTree: TypeAlias = dict[str, "FieldGroupTree"] | list[str] | None


def recursive_field_group(elements: set[str] | list[str], level: int = 0) -> FieldGroupTree:
    """
    Recursively groups field names by their hierarchical components, separated by -.
    This function takes a set of field names (as strings), where each field name may represent
    a hierarchy separated by - (e.g., "foo-bar-baz"). It groups the fields at each level of the
    hierarchy, building a nested dictionary structure that represents the grouping tree.
    Args:
        elements (set[str] | list[str]): A set or list of field name strings to group.
        level (int, optional): The current depth in the hierarchy (used for recursion).
        Defaults to 0.
    Returns:
        FieldGroupTree: A nested dictionary representing the grouped fields,
        where each key is a component
        at the current hierarchy level, and each value is either:
            - None, if the group is a leaf node or cannot be further subdivided,
            - or another nested dictionary for further grouping.
        Returns an empty list if the input is empty.
    """
    if not elements:
        return []

    grouped: dict[str, list] = defaultdict(list)

    for element in elements:
        parts: list[str] = element.split("-")
        if len(parts) > level:
            key: str = parts[level]
            grouped[key].append(element)

    if all(len(val) == 1 for val in grouped.values()):
        return None

    result: dict[str, Any] = {}
    for key, group_elements in grouped.items():
        unique_tags: set[str] = set(e for e in group_elements)

        # If is the last level
        if len(unique_tags) == 1 or all(len(e.split("-")) <= level + 1 for e in group_elements):
            result[key] = None
        # If the branch does continue then open it recursively
        else:
            result[key] = recursive_field_group(group_elements, level + 1)

    return result


def clean_empty_nodes(data: Any) -> Any | str:
    """
    Recursively removes keys from dictionaries whose values are None or empty dictionaries.
    If a dictionary becomes empty after cleaning, it is replaced with FieldsTag.END.

    Args:
        data (Any): The input data, typically a nested dictionary or other JSON-like structure.

    Returns:
        Union[Any, str]: The cleaned data with empty nodes replaced by FieldsTag.END,
                         or the original data if it is not a dictionary.
    """
    if isinstance(data, dict):
        cleaned_dict: dict[str, Any] = {}

        for key, value in data.items():
            cleaned_node = clean_empty_nodes(value)

            if cleaned_node is not None:
                cleaned_dict[key] = cleaned_node

        return cleaned_dict if cleaned_dict else FieldsTag.END

    return data


def flatten_dict(keys_dict: dict[str, Any], prefix: str = "") -> list[str]:
    """
    Recursively flattens a nested dictionary into a list of string keys,
    concatenating nested keys with -.
    Args:
        keys_dict (dict[str, Any]): The dictionary to flatten.
            Nested dictionaries are traversed recursively.
        prefix (str, optional): The prefix to prepend to each key, used during recursion.
            Defaults to "".
    Returns:
        list[str]: A list of flattened key strings, where nested keys are joined by -.
    Notes:
        - Keys are concatenated with - to represent their path in the nested dictionary.
        - Only keys whose value is `FieldsTag.END` are added to the result list.
        - If a value is a dictionary, the function recurses into it.
    """

    if not isinstance(keys_dict, dict):
        return []

    return_list: list[Any] = []

    for key, value in keys_dict.items():
        current_level: str = f"{prefix}-{key}" if prefix else key

        if value == FieldsTag.END:
            return_list.append(current_level)
        if isinstance(value, dict):
            return_list.extend(flatten_dict(value, current_level))

    return return_list


def get_initial_part_of_fields(
    client: Elasticsearch,
    keyword_name: str,
    index_name: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> list[str]:
    """
    Retrieves all unique initial values present in the specified keyword field across
    the target Elasticsearch indices.
    For example it can get the possible values of kubernetes.pod.name
    Args:
        client (Elasticsearch): An instance of the Elasticsearch client.
        keyword_name (str): The name of the keyword field to aggregate values from.
    Returns:
        list[str]: A list of unique initial values found for the specified field,
            processed and grouped.
    """

    all_field_names: set[str] = set()
    after_key: Any = None

    while True:
        request_body: dict[str, Any] = {
            "size": 0,
            "query": (
                {
                    "bool": {
                        "filter": (
                            [
                                {
                                    "range": {
                                        "@timestamp": {
                                            "format": "strict_date_optional_time",
                                            "gte": start_date,
                                            "lte": end_date,
                                        }
                                    }
                                }
                            ]
                            if start_date and end_date
                            else []
                        )
                    }
                }
                if start_date and end_date
                else {"match_all": {}}
            ),
            "aggs": {
                "result_values": {
                    "composite": {
                        # This is usually enough, and if it is not the request will
                        # be repeated automatically
                        "size": 10000,
                        "sources": [{"single_result": {"terms": {"field": keyword_name}}}],
                        **({"after": after_key} if after_key else {}),
                    }
                }
            },
        }

        response: Any = client.search(index=index_name, body=request_body)
        buckets: Any = response["aggregations"]["result_values"]["buckets"]

        for bucket in buckets:
            single_result: str = bucket["key"]["single_result"]
            all_field_names.add(single_result)

        after_key = response["aggregations"]["result_values"].get("after_key")
        if not after_key:
            break

    grouped_fields: FieldGroupTree = recursive_field_group(all_field_names)
    grouped_without_node_ends: Any = clean_empty_nodes(grouped_fields)
    result: list[str] = flatten_dict(grouped_without_node_ends)

    return result
