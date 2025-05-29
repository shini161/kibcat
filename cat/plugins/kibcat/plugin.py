from cat.mad_hatter.decorators import tool, hook
from cat.plugins.kibcat.utils.kibcat_api import (
    NotCertifiedKibana,
    get_spaces,
    get_dataviews,
    get_fields_list,
    group_fields,
    get_field_properties,
    get_field_possible_values,
)
from cat.plugins.kibcat.cat_logger import KibCatLogger

import json


@hook
def agent_prompt_prefix(prefix, cat):
    """Prompt prefix hook"""

    prefix = """Sei un aiutante per poter trovare dei log di un applicazione.
    I log sono salvati su elasticsearch e tu devi aiutare a generare delle query e filtri necessari a trovarli.
    Non rispondi a nulla che non c'entri con questo argomento.
    Rispondi in modo professionale, preciso, e conciso. Nessun giro di parole o informazioni aggiuntive. Vai diretto al punto."""

    return prefix


# Hardcoded data just for testing
URL = "http://kibana-logging-devops-pcto.stella.cloud.az.cgm.ag"
USERNAME = "kibana"
PASSWORD = "kibanaPassword"

SPACE_ID = "default"
DATA_VIEW_ID = "container-log*"


@tool(return_direct=True)
def add_filter(input, cat):  # [TODO]: add multiple filter options other than `is`
    """Aggiungi uno o più filtri deterministici alla ricerca su Kibana.

    I filtri sono strutturati in questo modo:
    [key] [operator] [value]
    dove [key] indica la chiave, ovvero il valore o variabile per cui filtrare
    [operator] indica la relazione tra i valori, i quali possibili valori sono (in lista JSON): ["is"]
    e infine [value] indica il valore a cui si sta comparando.

    input è una lista JSON di dizionari che indicano il filtraggio.
    Ogni dizionario ha varie proprietà:
    "key": la [key] da comparare
    "operator": l' [operator] da usare
    "value": il [value] per l'operatore

    ESEMPIO:
    user query: "Aggiungi un filtraggio in modo che example.test.kubernetes.num sia uguale a 8 e log.level sia di errore"
    input: "[{
    "key":"example.test.kubernetes.num",
    "operator":"is",
    "value":8
    },
    {
    "key":"log.level",
    "operator":"is"
    "value":"error"
    }]"
    """

    kibana = NotCertifiedKibana(base_url=URL, username=USERNAME, password=PASSWORD)

    spaces = get_spaces(kibana, LOGGER=KibCatLogger)

    if (not spaces) or (not any(space["id"] == SPACE_ID for space in spaces)):
        KibCatLogger.error("Specified space ID not found")
        return "Error during response"

    data_views = get_dataviews(kibana, LOGGER=KibCatLogger)

    if (not data_views) or (not any(view["id"] == DATA_VIEW_ID for view in data_views)):
        KibCatLogger.error("Specified data view not found")
        return "Error during response"

    # Get all the fields

    fields_list = get_fields_list(kibana, SPACE_ID, DATA_VIEW_ID, LOGGER=KibCatLogger)

    if not fields_list:
        KibCatLogger.error("Not found fields_list")
        return "Error during response"

    # Get cat input in json

    json_input = json.loads(input)
    # needed_fields = [element["key"] for element in json_input]

    # Group them with keywords if there are
    grouped_list = group_fields(fields_list)

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

    return f"```json\n{str(json.dumps(json_input,indent=4))}\n```"
