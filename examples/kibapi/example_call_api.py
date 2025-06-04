import os
from typing import Any, Optional, cast

from dotenv import load_dotenv

<<<<<<< HEAD:examples/kibapi/example_call_api.py
from kibapi import NotCertifiedKibana
from kiblog import BaseLogger
=======
from src.kibcat_api.kibcat_api import NotCertifiedKibana, get_field_properties
>>>>>>> main:examples/kibana_api/call_api_example.py

load_dotenv()

# Connection Details
BASE_URL = os.getenv("KIBANA_URL")
USERNAME = os.getenv("KIBANA_USERNAME")
PASS = os.getenv("KIBANA_PASS")

SPACE_ID = os.getenv("KIBANA_SPACE_ID")
DATA_VIEW_ID = os.getenv("KIBANA_DATA_VIEW_ID")
EXAMPLE_FIELD_NAME = os.getenv("EXAMPLE_FIELD_NAME")

# LOGGER
LOGGER = BaseLogger


def run_example() -> Optional[list[Any]]:
    """
    Connect to Kibana, validate space and data view, then fetch possible values for a given field.

    Returns:
        A list of possible values for the test field, or None on failure.
    """

    if not BASE_URL or not USERNAME or not PASS:
        msg = (
            "[example_call_api.py] - Missing required environment variables: KIBANA_URL,"
            "KIBANA_USERNAME or KIBANA_PASS"
        )
        LOGGER.message(msg)
        return None

    # Initialize Kibana API
    kibana = NotCertifiedKibana(base_url=BASE_URL, username=USERNAME, password=PASS)

    # Validate space
    spaces = kibana.get_spaces()
    if not spaces or not any(space.get("id") == SPACE_ID for space in spaces):
        msg = f"[example_call_api.py] - Specified Space ID '{SPACE_ID}' not found."
        LOGGER.error(msg)
        return None

    # Validate date view
    data_views = kibana.get_dataviews()
    if not data_views or not any(view.get("id") == DATA_VIEW_ID for view in data_views):
        msg = f"[example_call_api.py] - Specified data view ID '{DATA_VIEW_ID}' not found."
        LOGGER.error(msg)
        return None

    # Fetch and group fields
    if SPACE_ID is None or DATA_VIEW_ID is None:
        msg = "[example_call_api.py] - SPACE_ID or DATA_VIEW_ID are None."
        LOGGER.error(msg)
        raise ValueError(msg)

    fields_list = kibana.get_fields_list(SPACE_ID, DATA_VIEW_ID)
    if not fields_list:
        msg = "[example_call_api.py] - No fields found for the specified data view."
        LOGGER.error(msg)
        return None

    # Test: retrieve field properties and possible values
    field_properties = get_field_properties(fields_list, EXAMPLE_FIELD_NAME) # type: ignore
    if not field_properties:
        msg = f"[example_call_api.py] - Field '{EXAMPLE_FIELD_NAME}' not found in fields list."
        LOGGER.error(msg)
        return None

    try:
        values = kibana.get_field_possible_values(SPACE_ID, DATA_VIEW_ID, field_properties)
        return cast(Optional[list[Any]], values)
    except Exception as e:
        msg = f"[example_call_api.py] - Error fetching values for field '{EXAMPLE_FIELD_NAME}': {e}"
        LOGGER.error(msg)
        return None


if __name__ == "__main__":
    print("🔍 Running Kibana field value fetch example...")

    values = run_example()

    if values is not None:
        LOGGER.message("✅ Possible values:")
        for value in values:
            LOGGER.message(f"• {value}")
    else:
        msg = "[example_call_api.py] - Example failed."
        LOGGER.error(msg)
