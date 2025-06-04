"""
Utility functions for the kibapi package.
"""

from collections import defaultdict
from typing import Any


def group_fields(fields: list[dict[str, Any]]) -> list[list[str]]:
    """Groups fields with their keyword subfields
    [[
        "stream",
        "stream.keyword"
    ],
    [
        "tags",
        "tags.keyword"
    ]]
    """
    groups_dict: dict[str, list[str]] = defaultdict(list)

    for field in fields:
        # Get field name
        name = field.get("name")

        # Get field parent if it exists
        parent = field.get("subType", {}).get("multi", {}).get("parent")
        if name and parent:
            groups_dict[parent].append(name)

    grouped: set[str] = set()
    result: list[list[str]] = []

    for field in fields:
        name = field.get("name")
        if not name:
            continue

        if name in groups_dict:
            group = [name] + groups_dict[name]
            result.append(group)
            grouped.update(group)
        elif name not in grouped:
            result.append([name])
            grouped.add(name)

    return result


def get_field_properties(fields: list[dict[str, Any]], target_field: str) -> dict[str, Any]:
    """Returns the properties of a field given its name from a list of field definitions."""
    try:
        return next((d for d in fields if d.get("name") == target_field))
    except StopIteration:
        return {}
