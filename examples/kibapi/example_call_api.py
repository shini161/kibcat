"""Example script to connect to Kibana, validate environment and fetch field values."""

import os
from typing import Any, Type, cast

from dotenv import load_dotenv

from kibapi import NotCertifiedKibana, get_field_properties
from kiblog import BaseLogger

load_dotenv()

# Connection Details
BASE_URL = os.getenv("KIBANA_URL")
USERNAME = os.getenv("KIBANA_USERNAME")
PASS = os.getenv("KIBANA_PASS")

SPACE_ID = os.getenv("KIBANA_SPACE_ID")
DATA_VIEW_ID = os.getenv("KIBANA_DATA_VIEW_ID")
EXAMPLE_FIELD_NAME = os.getenv("EXAMPLE_FIELD_NAME")


def run_example(logger: Type[BaseLogger] | None = None) -> list[Any] | None:
    """
    Connect to Kibana, validate space and data view, then fetch possible values for a given field.

    Returns:
        A list of possible values for the test field, or None on failure.
    """

    if not BASE_URL or not USERNAME or not PASS:
        msg = "[example.kibapi] - Missing required environment variables: KIBANA_URL, KIBANA_USERNAME or KIBANA_PASS"
        if logger:
            logger.message(msg)
        return None

    # Initialize Kibana API
    kibana = NotCertifiedKibana(base_url=BASE_URL, username=USERNAME, password=PASS)

    # Validate space
    spaces = kibana.get_spaces()
    if not spaces or not any(space.get("id") == SPACE_ID for space in spaces):
        msg = f"[example.kibapi] - Specified Space ID '{SPACE_ID}' not found."
        if logger:
            logger.error(msg)
        return None

    # Validate date view
    data_views = kibana.get_dataviews()
    if not data_views or not any(view.get("id") == DATA_VIEW_ID for view in data_views):
        msg = f"[example.kibapi] - Specified data view ID '{DATA_VIEW_ID}' not found."
        if logger:
            logger.error(msg)
        return None

    # Fetch and group fields
    if SPACE_ID is None or DATA_VIEW_ID is None:
        msg = "[example.kibapi] - SPACE_ID or DATA_VIEW_ID are None."
        if logger:
            logger.error(msg)
        raise ValueError(msg)

    fields_list = kibana.get_fields_list(SPACE_ID, DATA_VIEW_ID)
    if not fields_list:
        msg = "[example.kibapi] - No fields found for the specified data view."
        if logger:
            logger.error(msg)
        return None

    # Test: retrieve field properties and possible values
    field_properties = get_field_properties(fields_list, EXAMPLE_FIELD_NAME)  # type: ignore
    if not field_properties:
        msg = f"[example.kibapi] - Field '{EXAMPLE_FIELD_NAME}' not found in fields list."
        if logger:
            logger.error(msg)
        return None

    try:
        result = kibana.get_field_possible_values(SPACE_ID, DATA_VIEW_ID, field_properties)
        return cast(list[Any] | None, result)
    except Exception as e:  # pylint: disable=broad-exception-caught
        msg = f"[example.kibapi] - Error fetching values for field '{EXAMPLE_FIELD_NAME}': {e}"
        if logger:
            logger.error(msg)
        return None


if __name__ == "__main__":
    BaseLogger.message("[example.kibapi] Running Kibana field value fetch example...")

    values = run_example(BaseLogger)

    if values is not None:
        BaseLogger.message("✅ Possible values:")
        for value in values:
            BaseLogger.message(f"• {value}")
    else:
        BaseLogger.error("[example.kibapi] - Example failed.")
