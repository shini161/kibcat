Questo template è usato per generare l'url di kibana, a partire dai parametri:

| *Parametro* | *Descrizione* |
|------------|--------|
| `base_url` | url base di kibana |
| `start_time` | Tempo di inizio, formattato come `2025-05-09T18:02:40.258Z` |
| `end_time` | Tempo di fine, come prima |
| `visible_fields` | Lista delle field da visualizzare nei dati |
| `filters` | Dict contenente la field e il valore a cui deve corrispondere |
| `data_view_id` | ID del data view da usare |
| `search_query` | Query di ricerca in formato di Kibana |

Per ora è stato implementato solamente l'operatore `is`.

La funzione per renderizzare il json si trova in `src/json_template/builders.py`. Tramite il file `generate_url_example.py` è possibile testarne il funzionamento generando un link di kibana a partire dai parametri dati.

### Importante:
Per far funzionare correttamente l'import del template json è necessario che il file di template `url.json.jinja2` si trovi nello stesso path di `src/json_template/builders.py`.
