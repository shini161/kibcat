from cat.plugins.kibcat.imports.kibcat_api.kibcat_api import (
    NotCertifiedKibana,
    group_fields,
    get_field_properties,
)
from cat.plugins.kibcat.imports.json_template.builders import build_template
from cat.plugins.kibcat.prompts.builders import (
    build_refine_filter_json,
    build_form_data_extractor,
)
from cat.plugins.kibcat.imports.url_jsonifier.builders import build_rison_url_from_json
from cat.plugins.kibcat.imports.kibcat_types.parsed_kibana_url import ParsedKibanaURL
from cat.plugins.kibcat.utils.kib_cat_logger import KibCatLogger

from pydantic import BaseModel
from cat.experimental.form import CatForm, form

import json
import os
from datetime import datetime, timedelta, timezone
from typing import Any

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


###################################


class FilterItem(BaseModel):
    key: str
    operator: str = "is"
    value: str

class FilterData(BaseModel):
    start_time: int = 14400  # Default to 4 hours
    end_time: int = 0
    filters: list[FilterItem] = []

@form
class FilterForm(CatForm):
    description = "filter logs"
    model_class = FilterData
    start_examples = [
        "filter logs",
        "obtain logs",
        "show logs",
        "search logs"
    ]
    stop_examples = [
        "stop filtering logs",
        "not interested anymore",
    ]
    ask_confirm = False

    def submit(self, form_data: FilterData) -> dict[str, str]:
        """Handles the form submission."""
        
        # Check the variables
        env_check_result: str | None = check_env_vars()
        if env_check_result:
            KibCatLogger.error(env_check_result)
            return env_check_result

        # Initialize the Kibana API class
        kibana: NotCertifiedKibana = NotCertifiedKibana(
            base_url=URL, username=USERNAME, password=PASSWORD
        )

        # Get the list of spaces in Kibana
        spaces: list[dict[str, Any]] | None = kibana.get_spaces(LOGGER=KibCatLogger)

        # Check if the needed space exists, otherwise return the error
        if (not spaces) or (not any(space["id"] == SPACE_ID for space in spaces)):
            msg: str = "Specified space ID not found"

            KibCatLogger.error(msg)
            return msg

        # Get the dataviews from the Kibana API
        data_views: list[dict[str, Any]] | None = kibana.get_dataviews(LOGGER=KibCatLogger)

        # Check if the dataview needed exists, otherwise return the error
        if (not data_views) or (not any(view["id"] == DATA_VIEW_ID for view in data_views)):
            msg: str = "Specified data view not found"

            KibCatLogger.error(msg)
            return msg

        # Get all the fields using the Kibana API
        # Type is ignored because env variables are already checked using the check_env_vars function
        fields_list: list[dict[str, Any]] | None = kibana.get_fields_list(SPACE_ID, DATA_VIEW_ID, LOGGER=KibCatLogger)  # type: ignore

        # if the field list cant be loaded, return the error
        if not fields_list:
            msg: str = "Not found fields_list"

            KibCatLogger.error(msg)
            return msg

        json_input: dict = form_data.get("filters", {})

        # Group them with keywords if there are
        grouped_list: list[list[str]] = group_fields(fields_list)

        # Extract the requested fields that actually exist, to be showed
        requested_keys: set = {element["key"] for element in json_input}
        fields_to_visualize: list = [
            field["name"] for field in fields_list if field["name"] in requested_keys
        ]

        # Add to the visualize
        for key, _ in MAIN_FIELDS_DICT.items():
            if key not in fields_to_visualize:
                fields_to_visualize.append(key)

        # Associate a group to every field in this dict
        field_to_group: dict = {field: group for group in grouped_list for field in group}

        # Replace the key names with the possible keys in the input
        for element in json_input:
            key: str = element.get("key", "")
            element["key"] = field_to_group.get(key, [key])

        # Now add the list of possible values per each one of the keys using the Kibana API
        for element in json_input:
            key_fields: list = element.get("key", [])
            new_key: dict = {}

            for field in key_fields:
                # Get the field's properties
                field_properties: dict[str, Any] = get_field_properties(fields_list, field)

                # Get all the field's possible values
                # Type is ignored because env variables are already checked using the check_env_vars function
                possible_values: list[Any] = kibana.get_field_possible_values(
                    SPACE_ID, DATA_VIEW_ID, field_properties, LOGGER=KibCatLogger  # type: ignore
                )

                new_key[field] = possible_values

            element["key"] = new_key

        # Build the LLM query to filter the JSON to get the exact parameters to search on Kibana
        query_filter_data: str = build_refine_filter_json(
            str(json.dumps(json_input, indent=2)), LOGGER=KibCatLogger
        )

        # Call the cat using the query
        cat_response: str = (
            self.cat.llm(query_filter_data).replace("```json", "").replace("`", "")
        )

        try:
            json_response: dict = json.loads(cat_response)
            KibCatLogger.message("Cat JSON parsed correctly")

        except json.JSONDecodeError as e:
            msg: str = f"Cannot decode cat's JSON filtered - {e}"

            KibCatLogger.error(msg)
            return msg

        # Separate kibana query and filters
        filters_cat = json_response.get("filters", [])
        kql_cat = json_response.get("query", []).replace('"', '\\"') #TODO: remove queries if not specified

        KibCatLogger.message(f"Filters: {filters_cat}")
        KibCatLogger.message(f"Kibana query: {kql_cat}")

        # Calculate time start and end
        end_time: datetime = datetime.now(timezone.utc) - timedelta(minutes=form_data.get('end_time', 0))
        start_time: datetime = datetime.now(timezone.utc) - timedelta(minutes=form_data.get('start_time', 14400))

        start_time_str: str = format_time_kibana(start_time)
        end_time_str: str = format_time_kibana(end_time)

        # [TODO]: Here is needed to implement the possibility to set the operator, other than 'is'
        filters: list = [(element["key"], element["value"]) for element in filters_cat]

        # Type is ignored because env variables are already checked using the check_env_vars function
        result_dict: ParsedKibanaURL = build_template(
            URL + BASE_URL_PART,  # type: ignore
            start_time_str,
            end_time_str,
            fields_to_visualize,
            filters,
            DATA_VIEW_ID,  # type: ignore
            kql_cat,
            LOGGER=KibCatLogger,
        )

        url: str = build_rison_url_from_json(json_dict=result_dict, LOGGER=KibCatLogger)

        KibCatLogger.message(f"Generated URL:\n{url}")

        return {
            "output": f'Kibana <a href="{url}" target="_blank">URL</a>'
        }
    
    def extract(self):
        """Extracts the filter data from the form."""

        history = self.cat.working_memory.stringify_chat_history()

        json_str = self.cat.llm(build_form_data_extractor(
            conversation_history=history,
            LOGGER=KibCatLogger
        )).replace("```json", "").replace("`", "")

        response = json.loads(json_str)

        return {
            "start_time": response.get("start_time", 14400),
            "end_time": response.get("end_time", 0),
            "filters": response.get("filters", [])
        }
