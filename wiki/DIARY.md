_Alcuni file potrebbero non corrispondere esattamente alle descrizioni a causa di cambiamenti eseguiti col tempo sulla repo._

# 26/05/2025

Inizio analisi dell'URL di Kibana, encoder e decoder.

*Ora non esistente, in quanto non funzionante correttamente e sostituito da quello svolto nel [giorno 27/05/2025](#27052025).*

[kibana-url-encode/main.py](https://github.com/shini161/kibcat/blob/4cdde65917956da75fb754c5048ab9603e11831c/kibana-url-encode/main.py)
```python
import os
import json
from helper import decode_kibana_url, encode_kibana_url


ENCODE_URL = True # Change this to encode or decode the url here
KIBANA_URL = "url here"


if __name__ == "__main__":
    folder_path = os.path.join(os.path.dirname(__file__), "parts")

    if not os.path.exists(folder_path):
        os.mkdir(folder_path)

    base_url_path = os.path.join(folder_path, "baseurl.json")
    g_part_path = os.path.join(folder_path, "g_part.json")
    a_part_path = os.path.join(folder_path, "a_part.json")

    if ENCODE_URL:
        with open(base_url_path, "r") as f:
            base_url = json.load(f)["URL"]
        with open(g_part_path, "r") as f:
            g_obj = json.load(f)
        with open(a_part_path, "r") as f:
            a_obj = json.load(f)

        encoded_url = encode_kibana_url(base_url, g_obj, a_obj)

        print(f"Encoded Kibana URL: {encoded_url}")

    else:
        base_url, g_part, a_part = decode_kibana_url(KIBANA_URL)

        print(f"Base URL: {base_url}")

        with open(base_url_path, "w") as f:
            json.dump({"URL": base_url}, f, indent=2)
        with open(g_part_path, "w") as f:
            json.dump(g_part, f, indent=2)
        with open(a_part_path, "w") as f:
            json.dump(a_part, f, indent=2)

        print(f"Parts saved to {folder_path}")

```

L'URL di kibana è composto da un URL base, in questo caso: `https://kibana_example/app/discover`, e successivamente si hanno due parti codificate in `rison` indicate con `_g` e `_a`, che possono essere decodificate in un JSON:

Esempio _a:
```json
{
  "columns": [
    "example.id",
    "example.log.message",
    "example.namespace",
    "example.pod.name"
  ],
  "dataSource": {
    "dataViewId": "log*",
    "type": "dataView"
  },
  "filters": [],
  "grid": {
    "columns": {
      "@timestamp": {
        "width": 127
      },
      "example.id": {
        "width": 159
      },
      "example.log.message": {
        "width": 249
      },
      "example.namespace": {
        "width": 202
      }
    }
  },
  "interval": "auto",
  "query": {
    "language": "kuery",
    "query": "example.pod.name : \"backend\""
  },
  "sort": [
    [
      "@timestamp",
      "desc"
    ]
  ]
}
```

# 27/05/2025

Per poter generare URL di Kibana con i desiderati parametri è stato creato un [template `jinja2`](https://github.com/shini161/kibcat/blob/60c101874696f0e250c03abeb2d44e8b1d66ff87/json-template/url-template.json.jinja2), che serve a generare il `dict` da codificare in rison tramite la funzione `build_rison_url_from_json` in [url_jsonifier](https://github.com/shini161/kibcat/blob/60c101874696f0e250c03abeb2d44e8b1d66ff87/url_jsonifier/utils.py) per generare il link a Kibana.

Per renderizzare il template è stata creata la funzione `render_dict` in [load_template.py](https://github.com/shini161/kibcat/blob/60c101874696f0e250c03abeb2d44e8b1d66ff87/json-template/load_template.py) alla quale è possibile passare i parametri necessari per ottenere il dict json da utilizzare per l'url.

I parametri possibili sono:

| *Parametro* | *Descrizione* |
|------------|--------|
| `base_url` | url base di kibana |
| `start_time` | Tempo di inizio, formattato come `2025-05-09T18:02:40.258Z` |
| `end_time` | Tempo di fine, come prima |
| `visible_fields` | Lista delle field da visualizzare nei dati |
| `filters` | Dict contenente la field e il valore a cui deve corrispondere |
| `data_view_id` | ID del data view da usare |
| `search_query` | Query di ricerca in formato di Kibana |

Per ora è stato implementato solamente l'operatore `is` durante il filtraggio, ma in futuro sarà possibile aggiungere tutti gli operatori.

In questo esempio viene generato l'url di kibana che porta ad un filtraggio dei dati coi parametri specificati:

```python
    base_url = "https://kibana_example/app/discover"
    start_time = "2025-05-09T18:02:40.258Z"
    end_time = "2025-05-10T02:05:46.064Z"
    visible_fields = ["example.id", "example.log.message", "example.namespace",
                      "example.pod.name", "example.image.name", "example.log.level"]
    filters = [("example.namespace", "qa"),
               ("example.log.level", "ERROR")]
    data_view_id = "log*"
    search_query = "example.pod.name : \\\"backend\\\""

    result_dict = render_dict(base_url,
                              start_time,
                              end_time,
                              visible_fields,
                              filters,
                              data_view_id,
                              search_query)

    url = build_rison_url_from_json(json_dict=result_dict)

```

Invece per quanto riguarda l'API di Kibana è stato risolto l'errore del certificato creando un wrapper per la classe dell'API di Kibana su Python

[kibcat_api.py](https://github.com/shini161/kibcat/blob/71af1fec733497c02523e3e8594e6e49282eddd5/kibana-api/kibcat_api.py)
```python
class NotCertifiedKibana(Kibana):
    """Kibana class wrapper to disable SSL certificate"""

    def requester(self, **kwargs):
        headers = {
            "Content-Type": "application/json",
            "kbn-xsrf": "True",
        } if not "files" in kwargs else {
            "kbn-xsrf": "True",
        }
        auth = (self.username, self.password) if (
            self.username and self.password) else None
        return requests.request(headers=headers, auth=auth, verify=False, **kwargs)

    def get(self, path):
        return self.requester(method="GET", url=f"{self.base_url}{path}")
```

Inoltre per poter ottenere la lista delle field per il filtraggio dei dati (quelle che sono circa 270 sull UI di Kibana) è stato trovato l'indirizzo dell'API: `"/s/{SPACE_ID}/internal/data_views/fields?pattern={DATA_VIEW_ID}"` dove `SPACE_ID` indica l'ID dello space, solitamente `default`, e `DATA_VIEW_ID` indica l'ID del data view da utilizzare, che al momento è `container-log*`

---

[URL JSONifier](https://github.com/shini161/kibcat/tree/71af1fec733497c02523e3e8594e6e49282eddd5/url_jsonifier) è il modulo utilizzato per convertire gli URL Rison di Kibana in JSON (oppure dict python) e viceversa.

È stata utilizzata la libreria [`prison`](https://pypi.org/project/prison/) per parsare il rison, regex per identificare gli argomenti dell'URL (ovvero la parte `_g` e la parte `_a`)

[url_jsonifier/utils.py](https://github.com/shini161/kibcat/blob/71af1fec733497c02523e3e8594e6e49282eddd5/url_jsonifier/utils.py)
```py
def parse_rison_url_to_json(url: str, path: str | None = None) -> Dict:
    """
    Parses a Kibana URL containing Rison-encoded `_g` and `_a` parameters in the fragment,
    decodes them into Python dictionaries, and optionally saves the result to a JSON file.

    Args:
        url (str): The full Kibana URL to parse.
        path (str, optional): If provided, the decoded data will be saved to this file path as JSON.

    Returns:
        dict: A dictionary with the following keys:
            - base_url (str): The part of the URL before the fragment.
            - _g (dict or None): Decoded `_g` parameter, or None if not present or failed to decode.
            - _a (dict or None): Decoded `_a` parameter, or None if not present or failed to decode.
    """

def build_rison_url_from_json(path: str | None = None, json_dict: Dict | None = None) -> str:
    """
    Reconstructs a Kibana URL with Rison-encoded _g and _a fragments from a JSON file or dictionary.

    Args:
        path (str, optional): Path to the JSON file containing base_url, _g, and _a. Defaults to None.
        json_dict (Dict, optional): Dictionary with base_url, _g, and _a. Used if path is not provided.

    Returns:
        str: The reconstructed Kibana URL with Rison-encoded _g and _a in the fragment.

    Raises:
        ValueError: If neither path nor json_dict is provided or if they contain invalid data.
    """
```

Sono stati aggiunti [test automatici](https://github.com/shini161/kibcat/tree/71af1fec733497c02523e3e8594e6e49282eddd5/tests) di workflow su github sul modulo di `url_jsonifier`

# 28/05/2025

Riguardo all'API di Kibana sono state create varie funzioni, nel file [kibcat_api.py](https://github.com/shini161/kibcat/blob/9c778cf51d0e522d9e5e6957f10a91b5e7a875d3/src/kibana_api/kibcat_api.py), per poter rendere più semplice la richiesta di dati a Kibana, da usare per poi generare gli URL tramite il Cat.

La funzione `get_spaces` serve ad ottenere tutti gli `space` di Kibana e in questo caso per verificare se quello che si vuole usare esista.

La funzione `get_dataviews` serve ad ottenere la lista dei `data view` su Kibana per verificare se quella necessaria esista.

La funzione `get_fields_list` chiama l'API di Kibana per ottenere la lista delle field con anche la tipologia e altri dati riguardanti le field.
In questo caso viene usata per ottenere la lista delle field e le keyword collegate a delle field specifiche.

La funzione `group_fields` si occupa di associare ad ogni field una eventuale keyword che la riguarda, per facilitare successivamente il passaggio di informazioni al Cat.

La funzione `get_field_properties` si occupa semplicemente di ricavare le proprietà di una specifica field, e serve per ricavare i possibili valori di quella field, tramite la funzione `get_field_possible_values` che fa una richiesta API a Kibana per ottenere dei possibili valori che una field specifica può assumere.

[Esempio: example.py](https://github.com/shini161/kibcat/blob/71af1fec733497c02523e3e8594e6e49282eddd5/kibana-api/example.py)

```python

if __name__ == "__main__":
    kibana = NotCertifiedKibana(
        base_url=URL, username=USERNAME, password=PASSWORD)

    spaces = get_spaces(kibana)

    if (not spaces) or (not any(space["id"] == SPACE_ID for space in spaces)):
        print("Specified space ID not found")
        exit(1)

    data_views = get_dataviews(kibana)

    if (not data_views) or (not any(view["id"] == DATA_VIEW_ID for view in data_views)):
        print("Specified data view not found")
        exit(1)

    fields_list = get_fields_list(kibana, SPACE_ID, DATA_VIEW_ID)
    grouped_list = group_fields(fields_list)

    field_name = "example.some.field"  # Random field just to test if everything works
    field_properties = get_field_properties(fields_list, field_name)

    values = get_field_possible_values(
        kibana, SPACE_ID, DATA_VIEW_ID, field_properties)

    print(values)

```

Inoltre è stata aggiunta una [classe base di logging](https://github.com/shini161/kibcat/blob/71af1fec733497c02523e3e8594e6e49282eddd5/logger/base_logger.py), per facilitare il log durante lo sviluppo sul Cat, semplicemente wrappando la classe base.

[base_logger.py](https://github.com/shini161/kibcat/blob/71af1fec733497c02523e3e8594e6e49282eddd5/logger/base_logger.py)

```python
class BaseKibCatLogger:
    """Base logger class for all functions in this repo.
    Will be wrapped by another class to use the cat's logger once in the plugin"""

    @staticmethod
    def message(message: str):
        print(message)

    @staticmethod
    def warning(message: str):
        print(f"WARNING: {message}")

    @staticmethod
    def error(message: str):
        print(f"ERROR: {message}")
```

Esempio di uso in [cat/plugins/kibcat/utils/kib_cat_logger.py](https://github.com/shini161/kibcat/blob/71af1fec733497c02523e3e8594e6e49282eddd5/container/cat/plugins/kibcat/cat_logger.py):

```python
from cat.log import log
from cat.plugins.kibcat.utils.base_logger import BaseKibCatLogger


class KibCatLogger(BaseKibCatLogger):

    @staticmethod
    def message(message: str):
        log.info(message)

    @staticmethod
    def warning(message: str):
        log.warning(message)

    @staticmethod
    def error(message: str):
        log.error(message)
```

# 29/05/2025

La repo è stata sottoposta ad un refactoring completo in modo da migliorare la struttura di file e il naming dei file e delle cartelle.

---

È stata creata la prima demo, ovvero un tool di esempio per il Cat, dentro a [plugin.py](https://github.com/shini161/kibcat/blob/5d39c4220c6725c13e423b300b6cd1cd93094d08/cat/plugins/kibcat/plugin.py)

```python
@tool(return_direct=True)
def add_filter(input, cat):  # [TODO]: add multiple filter options other than `is`
    """Aggiungi uno o più filtri deterministici alla ricerca su Kibana.
    ...
    """
```

Questo tool, essendo la prima versione funzionante, non ha ancora le funzionalità complete necessarie, e quindi per il suo funzionamento è necessario che l'utente specifichi il valore esatto della field nella query, per esempio in questo modo:

```text
aggiungi un filtro per example.field.example1 di debug e filtra per tutti i example.field.example2 di backend. inoltre il example.field.example3 deve essere qa. estendi la ricerca negli ultimi 2 giorni
```

In questo caso il gatto estrae la richiesta dell'utente in formato JSON

```json
{
    "action": "add_filter",
    "action_input": {
        "filters": [
            {
                "key": "example.field.example1",
                "operator": "is",
                "value": "debug"
            },
            {
                "key": "example.field.example2",
                "operator": "is",
                "value": "backend"
            },
            {
                "key": "example.field.example3",
                "operator": "is",
                "value": "qa"
            }
        ],
        "time": 2880
    }
}
```

Successivamente si usa l'API di Kibana sviluppata nei giorni precedenti per poter ottenere le varie keyword e i possibili valori di ogni field richiesta dall'utente, scrivendo il risultato in una stringa JSON.

```json
[
  {
    "key": {
      "example.field.example1": [
        "CRITICAL",
        "DEBUG",
        "ERROR",
        "INFO",
        "TRACE",
        "WARN",
        "error",
        "fatal",
        "info",
        "information"
      ]
    },
    "operator": "is",
    "value": "debug"
  },
  {
    "key": {
      "example.field.example2": [],
      "example.field.example2.keyword": [
        "example_0",
        "example_1",
        "example_2",
        "example_3",
        "example_4",
        "example_5",
        "example_6",
        "example_7",
        "example_8",
        "example_9"
      ]
    },
    "operator": "is",
    "value": "backend"
  },
  {
    "key": {
      "example.field.example3": [],
      "example.field.example3.keyword": [
        "example_0",
        "example_1",
        "example_2",
        "example_3",
        "example_4",
        "example_5",
        "example_6",
        "example_7",
        "example_8",
        "example_9"
      ]
    },
    "operator": "is",
    "value": "qa"
  }
]
```

Tutto questo JSON viene poi passato a una chiamata all'LLM con la richiesta di separarli in query di filtraggio e query di kibana. Il risultato di questa chiamata LLM sarà un ulteriore JSON.

```json
{
  "filters": [
    {
      "key": "example.field.example1",
      "operator": "is",
      "value": "DEBUG"
    }
  ],
  "query": "example.field.example2: \"backend\" AND example.field.example3: \"qa\""
}
```

Infine tramite le varie funzioni di codifica e decodifica degli URL sviluppate precedentemente, combinate con la funzione che genera il JSON URL da template, è possibile generare un URL di Kibana che porta alla pagina coi filtraggi desiderati, che il Cat darà come risposta in markdown:

```python
    return f"Kibana [URL]({url})"
```

Per esempio la richiesta di esempio specificata precedentemente porterà alla pagina di Kibana:

![Kibana](/assets/kibana_test_1.PNG)

# 04/06/2025 - 05/06/2025

Field come `kubernetes.pod.name` in cui i valori sono formattati secondo: `nome-**`, per esempio:

```txt
example-test-7784c589c5-x8xx6
example-test-7784c389c8-x8646
example-test-ab35c389c8-x8646
ex-2353-5353-3423
ex-2353-5353-8764
```

necessitano di un metodo differente per poter ottenere tutti i valori possibili, in quanto Kibana non può fornire la lista di tutti i valori essendo che molti `pod.name` con lo stesso nome possono avere il codice della seconda parte diverso.

Nell'esempio riportato sopra sarebbe quindi necessario estrarre i nomi in questo modo, per poterli usare a filtrare effettivamente solo i pod specifici:

```json
[
  "example-test",
  "ex"
]
```

Per risolvere questo problema è stato creato un nuovo modulo, [`kibfieldvalues`](https://github.com/shini161/kibcat/tree/cd6f208a55fe7917984675dd8c6e1609c18c325d/src/kibfieldvalues).

[fields.py](https://github.com/shini161/kibcat/blob/cd6f208a55fe7917984675dd8c6e1609c18c325d/src/kibfieldvalues/fields.py)
```py
def get_initial_part_of_fields(
    client: Elasticsearch,
    keyword_name: str,
    index_name: str,
    start_date: str | None = None,
    end_date: str | None = None,
) -> list[str]:
    """
    Retrieves all unique initial values present in the specified keyword field across
    the target Elasticsearch indices.
    For example it can get the possible values of kubernetes.pod.name
    Args:
        client (Elasticsearch): An instance of the Elasticsearch client.
        keyword_name (str): The name of the keyword field to aggregate values from.
    Returns:
        list[str]: A list of unique initial values found for the specified field,
            processed and grouped.
    """
```

La logica utilizzata per poter separare il nome del pod dalla parte identificativa, ovvero il "codice", inizia utilizzando l'API di Elastic per richiedere tutti i valori unici che quella field assume, che essendo relativamente pochi, è possibile elaborare in locale efficientemente.

Successivamente si cerca di trovare le field che iniziano con una stessa stringa, ma differiscono solamente per la parte finale di "codice".

Queste field vengono raggruppate e successivamente la parte di "codice" che differisce per ogni field viene rimossa, effettivamente ricavando la parte univoca che identifica il nome che si sta cercando.

Infine la funzione ritorna una lista di stringhe composta dai nomi univoci utilizzabili per eseguire il filtraggio.

---

Per aprire in una nuova scheda il link di Kibana, è stato necessario modificare il modo in cui il Cat risponde all'utente, sostituendo la sintassi di Markdown con HTML, in modo da poter specificare l'attributo `target="_blank"`.

[plugin.py](https://github.com/shini161/kibcat/commit/1c877d59ec7f4aaf51bf588282d7e70fd486a8d9#diff-2dff3f6ac541a0b1aaa81cfd9b39bff9beef4f25c31a978577191783ecfe4a14R309)
```python
return f'Kibana <a href="{url}" target="_blank">URL</a>'
```

---

Per permettere al Cat di restituire all'utente errori o avvisi per dati forniti non corretti o ambigui, il tool `add_filter` è stato rimosso, e sostituito con un *form*.

[plugin.py](https://github.com/shini161/kibcat/blob/02b80334585068a222d8779993d890ac06531c46/cat/plugins/kibcat/plugin.py#L151)
```python
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
        
        # Tutta la logica per la generazione dell'URL di Kibana
        url = ...

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
```

È stata sovrascritta la funzione `extract` per poter estrarre i dati dal messaggio dell'utente con un prompt personalizzato.

[form_data_extractor.jinja2](https://github.com/shini161/kibcat/blob/02b80334585068a222d8779993d890ac06531c46/cat/plugins/kibcat/prompts/templates/form_data_extractor.jinja2)
```
{% raw %}Estrai dalla conversazione dei filtri deterministici da applicare alla ricerca su Kibana, e restituisci un JSON strutturato.

I filtri sono strutturati in questo modo:
[key] [operator] [value]
dove [key] indica la chiave, ovvero il valore o variabile per cui filtrare
[operator] indica la relazione tra i valori, i quali possibili valori sono (in lista JSON): ["is"]
e infine [value] indica il valore a cui si sta comparando.

FORMATO:
L'output che devi ritornare è un dict JSON contenente tre elementi, "filters", "start_time" e "end_time":
# "filters"
"filters": una lista di dizionari che indicano il filtraggio.
Ogni dizionario ha varie proprietà:
"key": la [key] da comparare
"operator": l' [operator] da usare
"value": il [value] per l'operatore
# "start_time" 
"start_time": indica fino a quanto tempo fa estendere la ricerca in *minuti* __se l'utente non specifica questo parametro, è 14400__.
# "end_time"
"end_time": indica fino a quanto tempo estendere la ricerca in *minuti* __se l'utente non specifica questo parametro, è 0__.

CONVERSAZIONE:
{% endraw %}{{ conversation_history }}{% raw %}

ESEMPIO:
conversazione: "Aggiungi un filtraggio in modo che example.test.kubernetes.num sia uguale a 8 e log.level sia di errore negli ultimi 50 minuti"
output: "{
"filters": [{
"key":"example.test.kubernetes.num",
"operator":"is",
"value":8
},
{
"key":"log.level",
"operator":"is",
"value":"error"
}],
"start_time": 50,
"end_time": 0
}"{% endraw %}
```

Di default, nel core del Cat, viene utilizzata [una funzione che, utilizzando un prompt contente il typing della classe specificata come `model`, estrae i dati dalla `conversation history`](https://github.com/cheshire-cat-ai/core/blob/abafac5cf0aba5dcb7bc3ce7b4d5ae981da15ed7/core/cat/experimental/form/cat_form.py#L200-L245).

---

Successivamente si è deciso di ampliare la possibilità dei filtri, aggiungendo tutti gli operatori di Kibana, ovvero: `IS`, `IS_NOT`, `IS_ONE_OF`, `IS_NOT_ONE_OF`, `EXISTS`, `NOT_EXISTS`.

Per fare questo è stato aggiornato il modulo [kibtemplate](https://github.com/shini161/kibcat/tree/cd6f208a55fe7917984675dd8c6e1609c18c325d/src/kibtemplate), aggiungendo [altri template](https://github.com/shini161/kibcat/tree/cd6f208a55fe7917984675dd8c6e1609c18c325d/src/kibtemplate/templates) `jinja2` per poter implementare tutti gli operatori.

Inoltre per rappresentare un filtro di Kibana è stata creata la classe `KibCatFilter`, che si trova all'interno di [kibcat_filter.py](https://github.com/shini161/kibcat/blob/cd6f208a55fe7917984675dd8c6e1609c18c325d/src/kibtemplate/kibcat_filter.py):

```python
from enum import Enum, auto


class FilterOperators(Enum):
    """Enumeration of filter operators used in KibCat filtering."""

    IS = auto()
    IS_NOT = auto()
    IS_ONE_OF = auto()
    IS_NOT_ONE_OF = auto()
    EXISTS = auto()
    NOT_EXISTS = auto()


class KibCatFilter:
    """
    Represents a filter condition for querying data.

    Attributes:
        field (str): The name of the field to filter on.
        operator (FilterOperators): The filter operation to apply.
        value (str | list[str]): The value(s) used for filtering.
    """

    field: str
    operator: FilterOperators
    value: str | list[str]

    def __init__(self, field: str, operator: FilterOperators, value: str | list[str]):
        self.field = field
        self.operator = operator
        self.value = value

```