"""Example script for generating a Kibana Discover URL."""

from typing import Type

from kiblog import BaseLogger
from kibtemplate import build_template, KibCatFilter, FilterOperators
from kiburl import build_rison_url_from_json

import os


# pylint: disable=too-many-positional-arguments
def generate_kibana_url(
    base_url: str,
    start_time: str,
    end_time: str,
    visible_fields: list[str],
    filters: list[KibCatFilter],
    data_view_id: str,
    search_query: str,
    logger: Type[BaseLogger] | None = None,
) -> str:
    """
    Generates a Kibana Discover URL based on provided parameters.

    Raises:
        RuntimeError: If rendering or URL building fails.
    """

    try:
        result_json_template = build_template(
            base_url=base_url,
            start_time=start_time,
            end_time=end_time,
            visible_fields=visible_fields,
            filters=filters,
            data_view_id=data_view_id,
            search_query=search_query,
            logger=logger,
        )
    except Exception as e:
        msg = f"[example.kibtemplate] - Failed to render template\n{e}"
        if logger:
            logger.error(msg)
        raise RuntimeError(msg) from e

    try:
        result = build_rison_url_from_json(json_dict=result_json_template)
    except Exception as e:
        msg = f"[example.kibtemplate] - Failed to build Rison URL\n{e}"
        if logger:
            logger.error(msg)
        raise RuntimeError(msg) from e

    return result


BASE_URL = "https://localhost:9200/discover"
START_TIME = "2025-05-09T18:02:40.258Z"
END_TIME = "2025-05-10T02:05:46.064Z"
VISIBLE_FIELDS = [
    "example.id",
    "log.message",
    "example.namespace",
    "example.name",
    "img.name",
    "log.level",
]
FILTERS = [
    KibCatFilter("example.namespace", FilterOperators.IS, "qa"),
    KibCatFilter("log.level", FilterOperators.IS_NOT, "ERROR"),
]
DATA_VIEW_ID = "logs*"
SEARCH_QUERY = 'example.name : \\"backend\\"'

LOGGER = BaseLogger

try:
    URL = generate_kibana_url(
        base_url=BASE_URL,
        start_time=START_TIME,
        end_time=END_TIME,
        visible_fields=VISIBLE_FIELDS,
        filters=FILTERS,
        data_view_id=DATA_VIEW_ID,
        search_query=SEARCH_QUERY,
        logger=LOGGER,
    )

    if LOGGER:
        LOGGER.message(URL)
except RuntimeError as e:
    if LOGGER:
        LOGGER.error(f"[example.kibtemplate] - Error while executing example\n{e}")
