import json
import os
import re
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from typing import Any, cast

import isodate
from cat.experimental.form import CatForm, CatFormState, form
from cat.mad_hatter.decorators import hook
from cat.plugins.kibcat.prompts.builders import (
    build_agent_prefix,
    build_form_check_exit_intent,
    build_form_confirm_message,
    build_form_data_extractor,
    build_form_end_message,
    build_form_print_message,
    build_refine_filter_json,
)
from cat.plugins.kibcat.utils import check_env_vars, format_T_in_date
from cat.plugins.kibcat.utils.generate_field_values import (
    automated_field_value_extraction,
    generate_field_to_group,
    verify_data_views_space_id,
)
from cat.plugins.kibcat.utils.kib_cat_logger import KibCatLogger
from cat.utils import parse_json
from elastic_transport import NodeConfig
from elasticsearch import Elasticsearch
from langchain_core.exceptions import OutputParserException
from pydantic import BaseModel

from kibapi import NotCertifiedKibana
from kibtemplate.builders import build_template
from kibtemplate.kibcat_filter import FilterOperators, KibCatFilter
from kibtypes.parsed_kibana_url import ParsedKibanaURL
from kiburl.builders import build_rison_url_from_json

# Environment Variables
URL = os.getenv("KIBANA_URL")
ELASTIC_URL = os.getenv("ELASTIC_URL")
BASE_URL_PART = os.getenv("KIBANA_BASE_URL_PART")
USERNAME = os.getenv("KIBANA_USERNAME")
PASSWORD = os.getenv("KIBANA_PASS")
SPACE_ID = os.getenv("KIBANA_SPACE_ID")
DATA_VIEW_ID = os.getenv("KIBANA_DATA_VIEW_ID")

FIELDS_JSON_PATH = os.getenv("FIELDS_JSON_PATH")


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
            return cast(dict[str, Any], json.load(f))

    except (OSError, json.JSONDecodeError) as e:
        # OSError covers file not found, permission issues, etc.
        # JSONDecodeError covers invalid JSON structure
        KibCatLogger.error(f"Error reading or parsing main fields JSON file: {e}")
        return {}


MAIN_FIELDS_DICT: dict[str, Any] | None = None

# TODO: move costants like start_time when we decide where to put them
DEFAULT_START_TIME: str = "PT4H"  # Default to 4 hours
DEFAULT_END_TIME: str = "PT0S"  # Default to now

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


######################## Hooks #######################
@hook
def after_cat_bootstrap(cat):
    check_env_vars(
        url=URL,
        elastic_url=ELASTIC_URL,
        base_url_part=BASE_URL_PART,
        username=USERNAME,
        password=PASSWORD,
        space_id=SPACE_ID,
        data_view_id=DATA_VIEW_ID,
    )


@hook
def agent_prompt_prefix(prefix, cat):
    """Prompt prefix hook"""

    prefix = build_agent_prefix(logger=KibCatLogger)

    return prefix


######################## FORMS #######################
# The query isnt used right now, maybe it will be implemented later
class QueryItem(BaseModel):
    key: str
    operator: str = "is"  # TODO: support other query operators
    value: str


class FilterData(BaseModel):
    start_time: str = DEFAULT_START_TIME
    end_time: str = DEFAULT_END_TIME
    filters: list[KibCatFilter] = []
    query: list[QueryItem] = []


@form
class FilterForm(CatForm):  # type: ignore
    description = "filter logs"
    model_class = FilterData
    start_examples = ["filter logs", "obtain logs", "show logs", "search logs"]
    # stop_examples not needed anymore
    ask_confirm = True

    _state = CatFormState.INCOMPLETE

    _kibana: NotCertifiedKibana
    _elastic: Elasticsearch

    def __init__(self, cat):
        # Initialize the NotCertifiedKibana instance with the provided credentials
        assert URL is not None
        assert USERNAME is not None
        assert PASSWORD is not None
        self._kibana = NotCertifiedKibana(base_url=URL, username=USERNAME, password=PASSWORD, logger=KibCatLogger)

        # Initialize Elastic instance
        assert ELASTIC_URL is not None
        node_config: NodeConfig = NodeConfig(
            scheme="https",
            host=ELASTIC_URL.split("://")[-1].split(":")[0],
            port=443,
            verify_certs=False,
        )

        self._elastic: Elasticsearch = Elasticsearch(
            [node_config],
            basic_auth=(USERNAME, PASSWORD),
        )

        self._fields_list: list[dict[str, Any]] = []

        # Get all the fields using the Kibana API
        # Type is ignored because env variables are already checked using the check_env_vars function
        assert SPACE_ID is not None
        assert DATA_VIEW_ID is not None
        optional_fields_list: list[dict[str, Any]] | None = self._kibana.get_fields_list(
            space_id=SPACE_ID, data_view_id=DATA_VIEW_ID
        )

        if not optional_fields_list:
            self._fields_list = []
        else:
            self._fields_list = optional_fields_list

        verify_result: str | None = verify_data_views_space_id(
            kibana=self._kibana,
            space_id=SPACE_ID,
            data_view_id=DATA_VIEW_ID,
            fields_list=self._fields_list,
            logger=KibCatLogger,
        )
        if verify_result:
            return verify_result

        # Associate a group to every field in this dict
        field_to_group: dict[str, Any] = generate_field_to_group(self._fields_list)

        global MAIN_FIELDS_DICT
        MAIN_FIELDS_DICT = get_main_fields_dict()

        new_main_fields: dict[str, Any] = {}

        # Replace the key names with the possible keys in the input
        for key, element in MAIN_FIELDS_DICT.items():
            description: str = element

            element_field_group = field_to_group.get(key, [key])
            possible_vals: dict[str, Any] = automated_field_value_extraction(
                element_field=element_field_group,
                data_view_id=DATA_VIEW_ID,
                space_id=SPACE_ID,
                fields_list=self._fields_list,
                kibana=self._kibana,
                elastic=self._elastic,
                logger=KibCatLogger,
            )

            new_main_fields[key] = {
                "description": description,
                "possible_values": possible_vals,
            }

        MAIN_FIELDS_DICT = new_main_fields

        super().__init__(cat)

    def next(self):
        # If state is WAIT_CONFIRM, check user confirm response..
        if self._state == CatFormState.WAIT_CONFIRM:
            if self.check_exit_intent():
                self._state = CatFormState.CLOSED
            else:
                self._state = CatFormState.INCOMPLETE

        if self.check_exit_intent():
            self._state = CatFormState.CLOSED

        # If the state is INCOMPLETE, execute model update
        # (and change state based on validation result)
        if self._state == CatFormState.INCOMPLETE:
            self.update()

        # If state is COMPLETE, ask confirm (or execute action directly)
        if self._state == CatFormState.COMPLETE:
            self._state = CatFormState.WAIT_CONFIRM

        # if state is still INCOMPLETE, recap and ask for new info
        return self.message()

    def _parse_filters(self, filters: list[Any]) -> list[KibCatFilter]:
        if not isinstance(filters, list):
            filters = []

        for index, filter_item in enumerate(filters):
            filter_item["operator"] = FilterOperators[filter_item.get("operator", "is").upper()]
            filters[index] = KibCatFilter(**filter_item)
        return filters

    def extract(self):
        """Extracts the filter data from the form."""

        history = self.cat.working_memory.stringify_chat_history()
        main_fields_str: str = json.dumps(MAIN_FIELDS_DICT, indent=2)
        operators_str: str = json.dumps([op.name.lower() for op in FilterOperators], indent=2)

        try:
            response = parse_json(
                self.cat.llm(
                    build_form_data_extractor(
                        conversation_history=history,
                        main_fields_str=main_fields_str,
                        operators_str=operators_str,
                        logger=KibCatLogger,
                    )
                )
            )
        except OutputParserException as e:
            KibCatLogger.error(f"Failed to parse JSON: {e}")
            return

        return {
            "start_time": response.get("start_time", DEFAULT_START_TIME),
            "end_time": response.get("end_time", DEFAULT_END_TIME),
            # Query is not used, only filters are
            "query": [],  # TODO: extract query from conversation using extractor template
            "filters": self._parse_filters(response.get("filters", [])),
        }

    def _generate_base_message(self) -> str:
        """Generates the base message for form incomplete response."""
        dump_obj = deepcopy(self._model)
        dump_obj["filters"] = [filter_element.model_dump() for filter_element in dump_obj["filters"]]

        input_data = json.dumps(
            {
                "errors": self._errors,
                "form_data": dump_obj,
            },
            indent=2,
            ensure_ascii=False,
        ).replace("`", "")

        prompt = build_form_print_message(
            conversation_history=self.cat.working_memory.stringify_chat_history(),
            input_data_str=input_data,
        )
        return cast(str, self.cat.llm(prompt))

    def validate(self):
        """Validate form data"""
        self._missing_fields: list[Any] = []
        self._errors = []

        # Validate start_time
        if "start_time" in self._model:
            start_time = self._model["start_time"]
            if not isinstance(start_time, str):
                self._errors.append("start_time: must be a string in ISO 8601 Duration Format")
                del self._model["start_time"]

        # Validate end_time
        if "end_time" in self._model:
            end_time = self._model["end_time"]
            if not isinstance(end_time, str):
                self._errors.append("end_time: must be a string in ISO 8601 Duration Format")
                del self._model["end_time"]

            def to_timedelta(d: timedelta | Any) -> timedelta:
                return d if isinstance(d, timedelta) else d.totimedelta(start=datetime.now())

            # Check if end_time is less than start_time
            if "start_time" in self._model and to_timedelta(
                isodate.parse_duration(format_T_in_date(end_time))
            ) > to_timedelta(isodate.parse_duration(format_T_in_date(self._model["start_time"]))):
                # self._errors.append("end_time: must be less than or equal to start_time")
                # del self._model["end_time"]
                end_time_new = self._model["start_time"]

                self._model["start_time"] = self._model["end_time"]
                self._model["end_time"] = end_time_new

        verify_result: str | None = verify_data_views_space_id(
            kibana=self._kibana,
            space_id=cast(str, SPACE_ID),
            data_view_id=cast(str, DATA_VIEW_ID),
            fields_list=self._fields_list,
            logger=KibCatLogger,
        )
        if verify_result:
            return verify_result

        filters: dict[Any, Any] = deepcopy(self._model.get("filters", {}))

        # Associate a group to every field in this dict
        field_to_group: dict[str, Any] = generate_field_to_group(self._fields_list)

        # Replace the key names with the possible keys in the input
        for element in filters:
            key: str = element.field
            element_field_group = field_to_group.get(key, [key])
            element.field = automated_field_value_extraction(
                element_field=element_field_group,
                data_view_id=cast(str, DATA_VIEW_ID),
                space_id=cast(str, SPACE_ID),
                fields_list=self._fields_list,
                kibana=self._kibana,
                elastic=self._elastic,
                logger=KibCatLogger,
            )

        # TODO: validate ambiguous filters
        # TODO: move deterministic validation of accepted values out of the cat
        operators_str: str = json.dumps([op.name.lower() for op in FilterOperators], indent=2)
        filter_data: str = build_refine_filter_json(
            json_input=json.dumps(
                [filter_element.model_dump() for filter_element in filters],
                indent=2,
            ),
            operators_str=operators_str,
            logger=KibCatLogger,
        )

        # Call the cat using the query
        cat_response: str = self.cat.llm(filter_data).replace("```json", "").replace("`", "")

        try:
            # Call the cat using the query
            json_cat_response: dict[Any, Any] = parse_json(self.cat.llm(filter_data))
            KibCatLogger.message("Cat JSON parsed correctly")

            if "errors" in json_cat_response:
                for error in json_cat_response["errors"]:
                    self._errors.append(error)
                self._state = CatFormState.INCOMPLETE
                return
            else:
                # Update model with the filtered data
                self._model["filters"] = self._parse_filters(deepcopy(json_cat_response)["filters"])

        except OutputParserException as e:
            msg = f"Cannot decode cat's JSON filtered - {e}"
            KibCatLogger.error(msg)
            self._errors.append(msg)
            self._state = CatFormState.INCOMPLETE
            return

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
        form_data_filters: dict[Any, KibCatFilter] = self._model.get("filters", [])
        form_data_kql = ""  # TODO: implement support for queries from scratch, from the form data for queries

        requested_keys: set[str] = {element.field for element in form_data_filters}
        fields_to_visualize: list[str] = [
            field["name"] for field in self._fields_list if field["name"] in requested_keys
        ]

        # Add to the visualize
        for key, _ in cast(dict[str, Any], MAIN_FIELDS_DICT).items():
            if key not in fields_to_visualize:
                fields_to_visualize.append(key)

        KibCatLogger.message(f"Filters: {form_data_filters}")
        KibCatLogger.message(f"Kibana query: {form_data_kql}")

        # Calculate time start and end
        end_time: datetime = datetime.now(timezone.utc) - isodate.parse_duration(
            format_T_in_date(duration=self._model.get("end_time", "PT0S"))
        )
        start_time: datetime = datetime.now(timezone.utc) - isodate.parse_duration(
            format_T_in_date(duration=self._model.get("start_time", "PT0S"))
        )

        start_time_str: str = format_time_kibana(dt=start_time)
        end_time_str: str = format_time_kibana(dt=end_time)

        # Type is ignored because env variables are already checked using the check_env_vars function
        assert URL is not None
        assert BASE_URL_PART is not None
        result_dict: ParsedKibanaURL = build_template(
            base_url=URL + BASE_URL_PART,
            start_time=start_time_str,
            end_time=end_time_str,
            visible_fields=fields_to_visualize,
            filters=self._model.get("filters", []),
            data_view_id=DATA_VIEW_ID,  # type: ignore
            search_query=form_data_kql,
            logger=KibCatLogger,
        )

        url: str = build_rison_url_from_json(json_dict=result_dict, logger=KibCatLogger)

        KibCatLogger.message(f"Generated URL:\n{url}")

        applied_filters = json.dumps(
            [filter_element.model_dump() for filter_element in self._model.get("filters", "[]")],
            indent=2,
        )

        prompt = build_form_confirm_message(
            conversation_history=self.cat.working_memory.stringify_chat_history(),
            applied_filters=applied_filters,
            logger=KibCatLogger,
        )
        ask_confirm_message = self.cat.llm(prompt)

        output_html = f'<a href="{url}" target="_blank">🔗 Kibana URL</a>\n<hr/>\n{ask_confirm_message}'
        output_html = re.sub(r"(<hr\s*/?>\s*){2,}", "<hr/>", output_html, flags=re.IGNORECASE)
        return {"output": output_html}

    def check_exit_intent(self) -> bool:
        # Get user message
        last_message = self.cat.working_memory.user_message_json.text

        # Queries the LLM and check if user is agree or not
        response = self.cat.llm(
            build_form_check_exit_intent(
                last_message=last_message,
                logger=KibCatLogger,
            )
        )
        return "true" in response.lower()

    def submit(self, form_data: FilterData | None) -> dict[str, str]:
        """
        Handles the form submission.
        This function will be called when user wants to exit the form, since the URL generation
        logic is already implemented in the confirm method.
        """

        prompt = build_form_end_message(self.cat.working_memory.stringify_chat_history())

        return {
            "output": self.cat.llm(prompt),
        }

    def message_closed(self):
        return self.submit(form_data=None)
