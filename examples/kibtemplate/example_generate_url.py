from typing import Optional, Type

from kiblog import BaseLogger
from kibtemplate import build_template
from kiburl import build_rison_url_from_json


def generate_kibana_url(
    base_url: str,
    start_time: str,
    end_time: str,
    visible_fields: list[str],
    filters: list[tuple[str, str]],
    data_view_id: str,
    search_query: str,
    LOGGER: Optional[Type[BaseLogger]] = None,
) -> str:
    """
    Generates a Kibana Discover URL based on provided parameters.

    Raises:
        RuntimeError: If rendering or URL building fails.
    """

    try:
        result_json_template = build_template(
            base_url,
            start_time,
            end_time,
            visible_fields,
            filters,
            data_view_id,
            search_query,
            LOGGER=LOGGER,
        )
    except Exception as e:
        msg = f"generate_example.py - Failed to render template\n{e}"
        if LOGGER:
            LOGGER.error(msg)
        raise RuntimeError(msg)

    try:
        url = build_rison_url_from_json(json_dict=result_json_template)
    except Exception as e:
        msg = f"generate_example.py - Failed to build Rison URL\n{e}"
        if LOGGER:
            LOGGER.error(msg)
        raise RuntimeError(msg)

    return url


if __name__ == "__main__":
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
    FILTERS = [("example.namespace", "qa"), ("log.level", "ERROR")]
    DATA_VIEW_ID = "logs*"
    SEARCH_QUERY = 'example.name : \\"backend\\"'

    LOGGER = BaseLogger

    try:
        url = generate_kibana_url(
            base_url=BASE_URL,
            start_time=START_TIME,
            end_time=END_TIME,
            visible_fields=VISIBLE_FIELDS,
            filters=FILTERS,
            data_view_id=DATA_VIEW_ID,
            search_query=SEARCH_QUERY,
            LOGGER=LOGGER,
        )

        if LOGGER is not None:
            LOGGER.message(url)
        else:
            print(url)
    except RuntimeError as e:
        msg = f"generate_example.py - Error while executing example\n{e}"
        if LOGGER is not None:
            LOGGER.error(msg)
        else:
            print(msg)
