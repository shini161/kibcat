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
)
from cat.plugins.kibcat.imports.url_jsonifier.builders import build_rison_url_from_json
from cat.plugins.kibcat.utils.kib_cat_logger import KibCatLogger

import json
import os
from datetime import datetime, timedelta, timezone

########## ENV variables ##########

URL = os.getenv("URL")
BASE_URL_PART = os.getenv("BASE_URL_PART")
USERNAME = os.getenv("USERNAME")
PASSWORD = os.getenv("PASSWORD")

SPACE_ID = os.getenv("SPACE_ID")
DATA_VIEW_ID = os.getenv("DATA_VIEW_ID")

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


###################################


@hook
def agent_prompt_prefix(prefix, cat):
    """Prompt prefix hook"""

    prefix = build_agent_prefix(LOGGER=KibCatLogger)

    return prefix


@tool(return_direct=True)
def add_filter(input, cat):  # [TODO]: add multiple filter options other than `is`
    """Aggiungi uno o più filtri deterministici alla ricerca su Kibana.

    I filtri sono strutturati in questo modo:
    [key] [operator] [value]
    dove [key] indica la chiave, ovvero il valore o variabile per cui filtrare
    [operator] indica la relazione tra i valori, i quali possibili valori sono (in lista JSON): ["is"]
    e infine [value] indica il valore a cui si sta comparando.

    input è un dict JSON contenente due elementi, "filters" e "time":
    # "filters"
    "filters": una lista di dizionari che indicano il filtraggio.
    Ogni dizionario ha varie proprietà:
    "key": la [key] da comparare
    "operator": l' [operator] da usare
    "value": il [value] per l'operatore
    # "time"
    "time" indica fino a quanto tempo fa estendere la ricerca in *minuti* __se l'utente non specifica questo parametro, è 14400__.

    ESEMPIO:
    user query: "Aggiungi un filtraggio in modo che example.test.kubernetes.num sia uguale a 8 e log.level sia di errore negli ultimi 50 minuti"
    input: "{
    "filters": [{
    "key":"example.test.kubernetes.num",
    "operator":"is",
    "value":8
    },
    {
    "key":"log.level",
    "operator":"is"
    "value":"error"
    }],
    "time": 50
    }"
    """

    # Check the variables

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

    fields_list = get_fields_list(kibana, SPACE_ID, DATA_VIEW_ID, LOGGER=KibCatLogger)

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
            possible_values = get_field_possible_values(
                kibana, SPACE_ID, DATA_VIEW_ID, field_properties, LOGGER=KibCatLogger
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

    result_dict = build_template(
        URL + BASE_URL_PART,
        start_time_str,
        end_time_str,
        existing_requested_fields,
        filters,
        DATA_VIEW_ID,
        kql_cat,
        LOGGER=KibCatLogger,
    )

    url = build_rison_url_from_json(json_dict=result_dict, LOGGER=KibCatLogger)

    KibCatLogger.message(f"Generated URL:\n{url}")

    return f"Kibana [URL]({url})"
    # return f"```json\n{cat_response}\n```"
    # return f"```json\n{str(json.dumps(json_input,indent=2))}\n```"
