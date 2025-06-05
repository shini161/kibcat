import json
import os
from datetime import datetime, timedelta, timezone
from typing import Any

import isodate
from pydantic import BaseModel

from cat.experimental.form import CatForm, CatFormState, form
from cat.mad_hatter.decorators import tool
from cat.plugins.kibcat.imports.kibapi import (NotCertifiedKibana,
                                               get_field_properties,
                                               group_fields)
from cat.plugins.kibcat.imports.kibtemplate.builders import build_template
from cat.plugins.kibcat.imports.kibtypes.parsed_kibana_url import \
    ParsedKibanaURL
from cat.plugins.kibcat.imports.kiburl.builders import \
    build_rison_url_from_json
from cat.plugins.kibcat.prompts.builders import (build_form_data_extractor,
                                                 build_refine_filter_json)
from cat.plugins.kibcat.utils.kib_cat_logger import KibCatLogger

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

# TODO: move costants like start_time when we decide where to put them
DEFAULT_START_TIME: int = 14400  # Default to 4 hours
DEFAULT_END_TIME: int = 0  # Default to now

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
    operator: str = "is"  # TODO: support other operators
    value: str


class QueryItem(BaseModel):
    key: str
    operator: str = "is"  # TODO: support other query operators
    value: str


class FilterData(BaseModel):
    start_time: int = DEFAULT_START_TIME
    end_time: int = DEFAULT_END_TIME
    filters: list[FilterItem] = []
    query: list[QueryItem] = []


@form  # type: ignore
class FilterForm(CatForm):
    description = "filter logs"
    model_class = FilterData  # type: ignore
    start_examples = ["filter logs", "obtain logs", "show logs", "search logs"]
    stop_examples = [
        "stop filtering logs",
        "not interested anymore",
    ]
    ask_confirm = True

    _kibana: NotCertifiedKibana

    def __init__(self, cat):
        # Initialize the NotCertifiedKibana instance with the provided credentials
        self._kibana = NotCertifiedKibana(
            base_url=URL, username=USERNAME, password=PASSWORD
        )

        # Get all the fields using the Kibana API
        # Type is ignored because env variables are already checked using the check_env_vars function
        optional_fields_list: list[dict[str, Any]] | None = self._kibana.get_fields_list(SPACE_ID, DATA_VIEW_ID, logger=KibCatLogger)  # type: ignore
        if not optional_fields_list:
            self._fields_list: list[dict[str, Any]] = []
        else:
            self._fields_list: list[dict[str, Any]] = optional_fields_list
        super().__init__(cat)

    def extract(self):
        """Extracts the filter data from the form."""

        history = self.cat.working_memory.stringify_chat_history()
        main_fields_str: str = json.dumps(MAIN_FIELDS_DICT, indent=2)

        json_str = (
            self.cat.llm(
                build_form_data_extractor(
                    conversation_history=history,
                    main_fields_str=main_fields_str,
                    logger=KibCatLogger,
                )
            )
            .replace("```json", "")
            .replace("`", "")
        )

        response = json.loads(json_str)

        return {
            "start_time": response.get("start_time", DEFAULT_START_TIME),
            "end_time": response.get("end_time", DEFAULT_END_TIME),
            "query": [],  # TODO: extract query from conversation using extractor template
            "filters": response.get("filters", []),
        }

    def _clean_model_data(self, filters):
        # Write updated values to the form model, in the format expected by the FilterData model
        self._model = FilterData(
            start_time=self._model.get("start_time", DEFAULT_START_TIME),
            end_time=self._model.get("end_time", DEFAULT_END_TIME),
            filters=[
                FilterItem(
                    key=(
                        list(filter_item["key"].keys())[0]
                        if isinstance(filter_item["key"], dict)
                        else filter_item["key"]
                    ),
                    operator=filter_item.get("operator", "is"),
                    value=filter_item["value"],
                )
                for filter_item in filters
            ],
            query=[
                QueryItem(
                    key=query_item["key"],
                    operator=query_item.get("operator", "is"),
                    value=query_item["value"],
                )
                for query_item in self._model.get("query", [])
            ],
        ).model_dump()

    def validate(self):
        """Validate form data"""
        self._missing_fields = []
        self._errors = []

        # Validate start_time
        if "start_time" in self._model:
            start_time = self._model["start_time"]
            if not isinstance(start_time, int) or start_time < 0:
                self._errors.append("start_time: must be a positive integer")
                del self._model["start_time"]

        # Validate end_time
        if "end_time" in self._model:
            end_time = self._model["end_time"]
            if not isinstance(end_time, int) or end_time < 0:
                self._errors.append("end_time: must be a positive integer")
                del self._model["end_time"]

            # Check if end_time is less than start_time
            if "start_time" in self._model and end_time > self._model["start_time"]:
                self._errors.append(
                    "end_time: must be less than or equal to start_time"
                )
                del self._model["end_time"]

        # Check the variables
        env_check_result: str | None = check_env_vars()
        if env_check_result:
            KibCatLogger.error(env_check_result)
            return env_check_result

        # Get the list of spaces in Kibana
        spaces: list[dict[str, Any]] | None = self._kibana.get_spaces(
            logger=KibCatLogger
        )

        # Check if the needed space exists, otherwise return the error
        if (not spaces) or (not any(space["id"] == SPACE_ID for space in spaces)):
            msg: str = "Specified space ID not found"

            KibCatLogger.error(msg)
            return msg

        # Get the dataviews from the Kibana API
        data_views: list[dict[str, Any]] | None = self._kibana.get_dataviews(
            logger=KibCatLogger
        )

        # Check if the dataview needed exists, otherwise return the error
        if (not data_views) or (
            not any(view["id"] == DATA_VIEW_ID for view in data_views)
        ):
            msg: str = "Specified data view not found"

            KibCatLogger.error(msg)
            return msg

        # if the field list cant be loaded, return the error
        if not self._fields_list:
            msg: str = "Not found fields_list"

            KibCatLogger.error(msg)
            return msg

        json_input: dict = self._model.get("filters", {})

        # Group them with keywords if there are
        grouped_list: list[list[str]] = group_fields(self._fields_list)

        # Associate a group to every field in this dict
        field_to_group: dict = {
            field: group for group in grouped_list for field in group
        }

        # Replace the key names with the possible keys in the input
        for element in json_input:
            key: str = element.get("key", "")
            element["key"] = field_to_group.get(key, [key])

        # Now add the list of possible values per each one of the keys using the Kibana API
        for element in json_input:
            key_fields: list = element.get("key", [])
            new_key: dict = {}

            # If there are two keys and last one ends with .keyword, add the .keyword field as well
            if len(key_fields) == 2 and key_fields[-1].endswith(".keyword"):
                # TODO: implement support for .keyword fields
                new_key[key_fields[0]] = []
            else:
                # If there are no two keys or the last one doesn't end with .keyword, just keep the original key
                field = key_fields[-1]
                # Get the field's properties
                field_properties: dict[str, Any] = get_field_properties(
                    self._fields_list, field
                )

                # Get all the field's possible values
                # Type is ignored because env variables are already checked using the check_env_vars function
                possible_values: list[Any] = self._kibana.get_field_possible_values(
                    SPACE_ID, DATA_VIEW_ID, field_properties, logger=KibCatLogger  # type: ignore
                )

                new_key[field] = possible_values

                # Remove original key
                del key_fields[0]

            element["key"] = new_key

        # TODO: validate ambiguous filters
        # TODO: move deterministic validation of accepted values out of the cat
        filter_data: str = build_refine_filter_json(
            str(json.dumps(json_input, indent=2)), logger=KibCatLogger
        )

        # Call the cat using the query
        cat_response: str = (
            self.cat.llm(filter_data).replace("```json", "").replace("`", "")
        )

        try:
            json_cat_response: dict = json.loads(cat_response)
            KibCatLogger.message("Cat JSON parsed correctly")

            # TODO: uncomment this when we implement .keyword fields support
            """
            if "errors" in json_cat_response:
                for error in json_cat_response["errors"]:
                    self._errors.append(error)
                self._state = CatFormState.INCOMPLETE
                self._clean_model_data(json_input)
                return
            else:
                json_input = json_cat_response
            """
        except json.JSONDecodeError as e:
            msg: str = f"Cannot decode cat's JSON filtered - {e}"

            KibCatLogger.error(msg)
            self._errors.append(msg)
            self._state = CatFormState.INCOMPLETE
            self._clean_model_data(json_input)
            return

        self._clean_model_data(json_input)

        if not self._errors and not self._missing_fields:
            self._state = CatFormState.COMPLETE
        else:
            self._state = CatFormState.INCOMPLETE

    def message_wait_confirm(self):
        """
        Generates URL with the provided information, sends it to the user and asks for confirmation.
        This function is called after the validation is successful (no errors or missing fields).
        If the user:
        - confirms: the conversation will continue with the submit method.
        - does not confirm: the form continues to call this method
          or the one that does the extraction (+validation) if new data is provided.
        """

        # Extract the requested fields that actually exist, to be showed
        form_data_filters: dict = self._model.get("filters", [])
        form_data_kql = ""  # TODO: implement support for queries from scratch, from the form data for queries

        requested_keys: set = {element["key"] for element in form_data_filters}
        fields_to_visualize: list = [
            field["name"]
            for field in self._fields_list
            if field["name"] in requested_keys
        ]

        # Add to the visualize
        for key, _ in MAIN_FIELDS_DICT.items():
            if key not in fields_to_visualize:
                fields_to_visualize.append(key)

        KibCatLogger.message(f"Filters: {form_data_filters}")
        KibCatLogger.message(f"Kibana query: {form_data_kql}")

        # Calculate time start and end
        end_time: datetime = datetime.now(timezone.utc) - \
            isodate.parse_duration(self._model.get("end_time", "PT0S"))
        start_time: datetime = datetime.now(timezone.utc) - \
            isodate.parse_duration(self._model.get("start_time", "PT0S"))

        start_time_str: str = format_time_kibana(start_time)
        end_time_str: str = format_time_kibana(end_time)

        # [TODO]: Here is needed to implement the possibility to set the operator, other than 'is'
        filters: list = [
            (element["key"], element["value"]) for element in form_data_filters
        ]

        # Type is ignored because env variables are already checked using the check_env_vars function
        result_dict: ParsedKibanaURL = build_template(
            URL + BASE_URL_PART,  # type: ignore
            start_time_str,
            end_time_str,
            fields_to_visualize,
            filters,
            DATA_VIEW_ID,  # type: ignore
            form_data_kql,
            logger=KibCatLogger,
        )

        url: str = build_rison_url_from_json(json_dict=result_dict, logger=KibCatLogger)

        KibCatLogger.message(f"Generated URL:\n{url}")

        return {
            "output": f'Kibana <a href="{url}" target="_blank">URL</a>\nVuoi apportare modifiche ai filtri o va bene così?',
            # TODO: replace hard-coded confirmation string
        }

    def submit(self, form_data: FilterData) -> dict[str, str]:
        """
        Handles the form submission.
        This function will be called when user wants to exit the form, since the URL generation
        logic is already implemented in the confirm method.
        """

        output_str = self.cat.llm("Write something like 'Thanks for using KibCat!'")
        # TODO: remove this part, decide what to do when form closes

        return {
            "output": output_str,
        }


###################################


@tool
def get_token_usage(input, cat):
    """Get the token usage for the current session."""
    input_tokens = cat.working_memory.model_interactions[1].input_tokens
    return f"Input tokens: {input_tokens}"
