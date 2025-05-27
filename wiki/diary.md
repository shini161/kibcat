# 26/05/2025

Inizio analisi dell'URL di Kibana, encoder e decoder.

[url encoder](/kibana-url-encode)
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

L'URL di kibana è composto da un URL base, in questo caso: `https://kibana-logging-devops-pcto.stella.cloud.az.cgm.ag/app/discover`, e successivamente si hanno due parti codificate in `rison` indicate con `_g` e `_a`, che possono essere decodificate in un JSON:

Esempio _a:
```json
{
  "columns": [
    "agent.id",
    "cometa.log.message",
    "kubernetes.namespace",
    "kubernetes.pod.name"
  ],
  "dataSource": {
    "dataViewId": "container-log*",
    "type": "dataView"
  },
  "filters": [],
  "grid": {
    "columns": {
      "@timestamp": {
        "width": 127
      },
      "agent.id": {
        "width": 159
      },
      "cometa.log.message": {
        "width": 249
      },
      "kubernetes.namespace": {
        "width": 202
      }
    }
  },
  "interval": "auto",
  "query": {
    "language": "kuery",
    "query": "kubernetes.pod.name : \"backend\""
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

Per poter generare URL di Kibana con i desiderati parametri è stato creato un [template `jinja2`](/json-template/url-template.json.jinja2), che serve a generare il `dict` da codificare in rison tramite la funzione `build_rison_url_from_json` in [utils.py](/url_jsonifier/utils.py) per generare il link a Kibana.

Per renderizzare il template è stata creata la funzione `render_dict` in [load_template.py](/json-template/load_template.py) alla quale è possibile passare i parametri necessari per ottenere il dict json da utilizzare per l'url.

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
    base_url = "https://kibana-logging-devops-pcto.stella.cloud.az.cgm.ag/app/discover"
    start_time = "2025-05-09T18:02:40.258Z"
    end_time = "2025-05-10T02:05:46.064Z"
    visible_fields = ["agent.id", "cometa.log.message", "kubernetes.namespace",
                      "kubernetes.pod.name", "container.image.name", "cometa.log.level"]
    filters = [("kubernetes.namespace", "qa"),
               ("cometa.log.level", "ERROR")]
    data_view_id = "container-log*"
    search_query = "kubernetes.pod.name : \\\"backend\\\""

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

[test.py](/kibana-api/test.py)
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