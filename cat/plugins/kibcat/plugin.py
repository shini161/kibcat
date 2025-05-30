from cat.mad_hatter.decorators import tool, hook
from cat.plugins.kibcat.imports.kibana_api.kibcat_api import (
    NotCertifiedKibana,
    get_spaces,
    get_dataviews,
    get_fields_list,
    group_fields,
    get_field_properties,
    get_field_possible_values,
)
from cat.plugins.kibcat.imports.json_template.builders import build_template
from cat.plugins.kibcat.prompts.builders import (
    build_refine_filter_json,
    build_agent_prefix,
    build_add_filter_tool_prefix,
)
from cat.plugins.kibcat.imports.url_jsonifier.builders import build_rison_url_from_json
from cat.plugins.kibcat.utils.kib_cat_logger import KibCatLogger

import json
import os
from datetime import datetime, timedelta, timezone
from typing import Callable, Any

########## ENV variables ##########

URL = os.getenv("KIBANA_URL")
BASE_URL_PART = os.getenv("KIBANA_BASE_URL_PART")
USERNAME = os.getenv("KIBANA_USERNAME")
PASSWORD = os.getenv("KIBANA_PASS")

SPACE_ID = os.getenv("KIBANA_SPACE_ID")
DATA_VIEW_ID = os.getenv("KIBANA_DATA_VIEW_ID")


def get_main_fields_dict() -> dict[str, Any]:
    """
    Load the main fields dictionary from the JSON file specified by the FIELDS_JSON_PATH environment variable.

    Returns:
        A dictionary parsed from the JSON file, or an empty dict if the path is not set or an error occurs.
    """
    fields_json_path: str | None = os.getenv("FIELDS_JSON_PATH")

    if not fields_json_path:
        KibCatLogger.error("FIELDS_JSON_PATH environment variable is not set.")
        return {}

    try:
        with open(fields_json_path, "r", encoding="utf-8") as f:
            return json.load(f)

    except (OSError, json.JSONDecodeError) as e:
        # OSError covers file not found, permission issues, etc.
        # JSONDecodeError covers invalid JSON structure
        KibCatLogger.error(f"Error reading or parsing main fields JSON file: {e}")
        return {}


MAIN_FIELDS_DICT = get_main_fields_dict()

###################################

############## Utils ##############


def format_time_kibana(dt: datetime) -> str:
    """
    Format a datetime object to a Kibana-compatible ISO 8601 string with milliseconds.

    Args:
        dt: A datetime object.

    Returns:
        A string formatted as 'YYYY-MM-DDTHH:MM:SS.mmmZ'.
    """
    return dt.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def check_env_vars() -> str | None:
    """Checks if the env variables loaded really exist.

    Returns:
        str | None: None if every variable has been loaded successfully, and str with the error message if a variable is missing
    """
    if not URL:
        msg = "URL parameter null"

        KibCatLogger.error(msg)
        return msg
    if not BASE_URL_PART:
        msg = "BASE_URL_PART parameter null"

        KibCatLogger.error(msg)
        return msg
    if not USERNAME:
        msg = "USERNAME parameter null"

        KibCatLogger.error(msg)
        return msg
    if not PASSWORD:
        msg = "PASSWORD parameter null"

        KibCatLogger.error(msg)
        return msg
    if not SPACE_ID:
        msg = "SPACE_ID parameter null"

        KibCatLogger.error(msg)
        return msg
    if not DATA_VIEW_ID:
        msg = "DATA_VIEW_ID parameter null"

        KibCatLogger.error(msg)
        return msg

    return None


def apply_add_filter_docstring() -> Callable:
    """
    A decorator to set dynamically the tool's docstring.
    """

    def decorator(func: Callable) -> Callable:
        main_fields_str: str = json.dumps(MAIN_FIELDS_DICT, indent=2)

        tool_prefix: str = build_add_filter_tool_prefix(
            main_fields_str=main_fields_str, LOGGER=KibCatLogger
        )

        func.__doc__ = tool_prefix
        return func

    return decorator


###################################


@hook
def agent_prompt_prefix(prefix, cat) -> str:
    """Prompt prefix hook"""

    prefix = build_agent_prefix(LOGGER=KibCatLogger)

    return prefix


@tool(return_direct=True)
@apply_add_filter_docstring()
def add_filter(input, cat):  # [TODO]: add multiple filter options other than `is`
    """The main tool for the first demo.

    This works with direct questions, like telling the cat the field and the value to filter it for.
    Also for the most used fields, written in the main_fields.json files the cat will automatically try to understand the needed field.

    The docstring the cat will use to register this tool is generated dynamically to include the main fields.
    """

    # Check the variables
    env_check_result = check_env_vars()
    if env_check_result:
        return env_check_result

    kibana = NotCertifiedKibana(base_url=URL, username=USERNAME, password=PASSWORD)

    spaces = get_spaces(kibana, LOGGER=KibCatLogger)

    if (not spaces) or (not any(space["id"] == SPACE_ID for space in spaces)):
        msg = "Specified space ID not found"

        KibCatLogger.error(msg)
        return msg

    data_views = get_dataviews(kibana, LOGGER=KibCatLogger)

    if (not data_views) or (not any(view["id"] == DATA_VIEW_ID for view in data_views)):
        msg = "Specified data view not found"

        KibCatLogger.error(msg)
        return msg

    # Get all the fields

    # Type is ignored because env variables are already checked using the check_env_vars function
    fields_list = get_fields_list(kibana, SPACE_ID, DATA_VIEW_ID, LOGGER=KibCatLogger)  # type: ignore

    if not fields_list:
        msg = "Not found fields_list"

        KibCatLogger.error(msg)
        return msg

    # Get cat input in json

    json_input_total = json.loads(input)
    json_input = json_input_total["filters"]

    time_ago = json_input_total["time"]
    # needed_fields = [element["key"] for element in json_input]

    # Group them with keywords if there are
    grouped_list = group_fields(fields_list)

    requested_keys = {element["key"] for element in json_input}
    existing_requested_fields = [
        field["name"] for field in fields_list if field["name"] in requested_keys
    ]

    field_to_group = {field: group for group in grouped_list for field in group}

    # Replace the key names with the possible keys in the input

    for element in json_input:
        key = element["key"]
        element["key"] = field_to_group.get(key, [key])

    # Now add the list of possible values per each one of the keys using the Kibana API

    for element in json_input:
        key_fields = element["key"]
        new_key = {}

        for field in key_fields:
            field_properties = get_field_properties(fields_list, field)
            # Type is ignored because env variables are already checked using the check_env_vars function
            possible_values = get_field_possible_values(
                kibana, SPACE_ID, DATA_VIEW_ID, field_properties, LOGGER=KibCatLogger  # type: ignore
            )

            new_key[field] = possible_values

        element["key"] = new_key

    query_filter_data = build_refine_filter_json(
        str(json.dumps(json_input, indent=2)), LOGGER=KibCatLogger
    )

    cat_response = cat.llm(query_filter_data).replace("```json", "").replace("`", "")
    json_response = json.loads(cat_response)

    filters_cat = json_response.get("filters", [])
    kql_cat = json_response.get("query", []).replace('"', '\\"')

    KibCatLogger.message(f"Filters: {filters_cat}")
    KibCatLogger.message(f"KibQuery: {kql_cat}")

    end_time = datetime.now(timezone.utc)
    start_time = end_time - timedelta(minutes=time_ago)

    start_time_str = format_time_kibana(start_time)
    end_time_str = format_time_kibana(end_time)

    # [TODO]: Here need to implement the possibility to set the operator, other than 'is'
    filters = [(element["key"], element["value"]) for element in filters_cat]

    # Type is ignored because env variables are already checked using the check_env_vars function
    result_dict = build_template(
        URL + BASE_URL_PART,  # type: ignore
        start_time_str,
        end_time_str,
        existing_requested_fields,
        filters,
        DATA_VIEW_ID,  # type: ignore
        kql_cat,
        LOGGER=KibCatLogger,
    )

    url = build_rison_url_from_json(json_dict=result_dict, LOGGER=KibCatLogger)

    KibCatLogger.message(f"Generated URL:\n{url}")

    return f"Kibana [URL]({url})"
    # return f"```json\n{cat_response}\n```"
    # return f"```json\n{str(json.dumps(json_input,indent=2))}\n```"
