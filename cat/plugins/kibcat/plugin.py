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
from cat.plugins.kibcat.imports.url_jsonifier.builders import build_rison_url_from_json
from cat.plugins.kibcat.utils.kib_cat_logger import KibCatLogger

import json
import os
from datetime import datetime, timedelta, timezone


@hook
def agent_prompt_prefix(prefix, cat):
    """Prompt prefix hook"""

    prefix = """Sei un aiutante per poter trovare dei log di un applicazione.
    I log sono salvati su elasticsearch e tu devi aiutare a generare delle query e filtri necessari a trovarli.
    Non rispondi a nulla che non c'entri con questo argomento.
    Rispondi in modo professionale, preciso, e conciso. Nessun giro di parole o informazioni aggiuntive. Vai diretto al punto."""

    return prefix


URL = os.getenv("URL")
BASE_URL_PART = os.getenv("BASE_URL_PART")
USERNAME = os.getenv("USERNAME")
PASSWORD = os.getenv("PASSWORD")

SPACE_ID = os.getenv("SPACE_ID")
DATA_VIEW_ID = os.getenv("DATA_VIEW_ID")


def format_time_kibana(dt):
    return dt.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


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

    query_filter_data = f"""
You are given a JSON input representing a list of filter candidates for a Kibana search. From this input, your goal is to generate two outputs:

1. A list of **filters**, using key-value pairs where the value exactly (or closely) matches a known value.
2. A **KQL query**, for approximate or unmatched values that should be used in free-text search.

---

### INPUT STRUCTURE (per item in list):

- `"key"`: a dictionary with one or more field names (some may have `.keyword` versions) as keys, and a list of known values for each.
- `"operator"`: the logical operator (e.g., "is").
- `"value"`: the value to match against known values.

---

### INSTRUCTIONS:

1. For each object in the input:
   - Check all fields in the `"key"` dictionary.
   - If the `"value"` (case-insensitive) **matches or is quite similar** to one of the listed possible values:
     - **If the match occurs in a `.keyword` field, you must prefer using that `.keyword` key** in the filter.
     - Otherwise, use the matching key as-is.
     - Use the matched value with original casing.
     - Add this to the `"filters"` list using the provided `"operator"`.

2. If the `"value"` does **not match or resemble any listed value** in any of the `"key"` fields (including `.keyword` ones):
   - Do **not** add a filter for this.
   - Instead, include a **free-text search** for the closest-matching field (prefer the non-`.keyword` version if available).
   - Add this in the `"query"` string in KQL format:
     - Format: `"field.name": "value"`

3. If multiple items require a query fallback, combine them using `AND`.

---

### EXPECTED OUTPUT FORMAT:

Return only a JSON object like this:

{{
  "filters": [
    {{
      "key": "field.name",
      "operator": "is",
      "value": "MatchedValue"
    }},
    ...
  ],
  "query": "field1.name: \"value1\" AND field2.name: \"value2\""
}}

---

### EXAMPLE INPUT:

[
  {{
    "key": {{
      "example.log.level": [
        "CRITICAL", "DEBUG", "ERROR", "INFO", "TRACE", "WARN",
        "error", "fatal", "info", "information"
      ]
    }},
    "operator": "is",
    "value": "warning"
  }},
  {{
    "key": {{
      "example.pod.name": [],
      "example.pod.name.keyword": [
        "container.level.testing.example2",
        "api.pod.level.testing"
      ]
    }},
    "operator": "is",
    "value": "backend"
  }}
]

---

### EXAMPLE OUTPUT:

{{
  "filters": [
    {{
      "key": "example.log.level",
      "operator": "is",
      "value": "WARN"
    }}
  ],
  "query": "example.pod.name: \"backend\""
}}

---

### INPUT JSON:
{str(json.dumps(json_input, indent=2))}
"""

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
