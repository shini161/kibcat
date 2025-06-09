from typing import Any, Type, cast

from elasticsearch import Elasticsearch
from kibapi import NotCertifiedKibana, get_field_properties, group_fields
from kibfieldvalues import get_initial_part_of_fields
from kiblog import BaseLogger


def automated_field_value_extraction(
    element_field: list[str],
    data_view_id: str,
    space_id: str,
    fields_list: list[dict[str, Any]],
    kibana: NotCertifiedKibana,
    elastic: Elasticsearch,
    logger: Type[BaseLogger] | None = None,
) -> dict[str, Any]:
    """Returns element.field, given an element.field pre-processed"""

    key_fields: list[str] = element_field
    new_key: dict[str, Any] = {}

    normal_field: str | None = None
    keyword_field: str | None = None

    for field in key_fields:
        if field.endswith(".keyword"):
            keyword_field = field
            continue
        normal_field = field

    if keyword_field:
        if logger:
            msg: str = f"Getting field {keyword_field} possible values using Elastic"
            logger.message(msg)

        keyword_field_values: list[str] = get_initial_part_of_fields(elastic, keyword_field, cast(str, data_view_id))

        new_key[keyword_field] = keyword_field_values
    else:
        if normal_field:
            if logger:
                msg: str = f"Getting field {normal_field} possible values using Kibana"
                logger.message(msg)

            field_properties: dict[str, Any] = get_field_properties(fields_list, normal_field)

            # Get all the field's possible values
            possible_values: list[Any] = kibana.get_field_possible_values(
                cast(str, space_id),
                cast(str, data_view_id),
                field_properties,
            )

            new_key[normal_field] = possible_values

    return new_key


def generate_field_to_group(fields_list: list[dict[str, Any]]):
    """Automatically generate the field-to-group dict"""

    # Group them with keywords if there are
    grouped_list: list[list[str]] = group_fields(fields_list)

    # Associate a group to every field in this dict
    field_to_group: dict[str, Any] = {field: group for group in grouped_list for field in group}

    return field_to_group


def verify_data_views_space_id(
    kibana: NotCertifiedKibana,
    space_id: str,
    data_view_id: str,
    fields_list: list[Any],
    logger: Type[BaseLogger] | None = None,
) -> str | None:
    """If an error occurs reurn the error string, else None"""

    # Get the list of spaces in Kibana
    spaces: list[dict[str, Any]] | None = kibana.get_spaces()

    # Check if the needed space exists, otherwise return the error
    if (not spaces) or (not any(space["id"] == space_id for space in spaces)):
        msg = "Specified space ID not found"

        if logger:
            logger.error(msg)
        return msg

    # Get the dataviews from the Kibana API
    data_views: list[dict[str, Any]] | None = kibana.get_dataviews()

    # Check if the dataview needed exists, otherwise return the error
    if (not data_views) or (not any(view["id"] == data_view_id for view in data_views)):
        msg: str = "Specified data view not found"

        if logger:
            logger.error(msg)
        return msg

    # if the field list cant be loaded, return the error
    if not fields_list:
        msg = "Not found fields_list"

        if logger:
            logger.error(msg)
        return msg

    return None
