# Conclusioni
In questa sezione riportiamo quali sono gli obiettivi raggiunti fino ad ora ripercorrendo brevemente la loro soluzione.

## Generazione URL di Kibana
Per poter generare URL di Kibana contenenti i filtri desiderati e l'eventuale query, è stato necessario identificare il formato in cui vengono salvate le informazioni all'interno degli URL.

È stato quindi trovato il formato, chiamato `rison`, ed è stato creato un parser in grado di estrarre le informazioni dall'URL e salvarle in formato JSON.

Grazie alle informazioni in formato JSON è stato possibilie ricavare il formato in cui vengono salvati i filtri e la query all'interno di esso, e quindi ricavare dei template per poter generare URL in formato JSON a partire dai parametri per la ricerca.

Infine è stato creato un encoder con l'obiettivo di trasformare l'output renderizzato del template JSON nuovamente in `rison` in modo da poter effettivamente generare l'URL.

## Field principali
Per poter eseguire il filtraggio in linguaggio naturale tramite LLM, è necessario fornire quali sono le field che vengono effettivamente usate con una breve descrizione, in modo da far si che l'LLM riesca a ricavare da una breve descrizione dell'utente la field alla quale si riferisce.

Per fare questo è stato creato un file JSON chiamato [`main_fields`](#main_fields), il quale contiene un dizionario composto dalle field maggiormente usate e una breve descrizione.

## Uso dell'API di Kibana e Elastic per ottenere i possibili valori delle field
In modo da riuscire a eseguire la fase di **validazione**, _che verrà spiegata successivamente_, è necessario avere i possibili valori che ogni field può assumere, così da avvertire l'utente che il valore che ha richiesto non esiste oppure che esso è ambiguo e si può avere su più field.

Per poter ricavare questi valori sono appunto state usate le API di **Kibana** e di **Elastic**. Per quanto riguarda l'API di Kibana, è stato necessario sovrascrivere la classe principale su python per rimuovere l'obbligo di usare i certificati.

Questa fase è facilmente rimpiazzabile, essendo gestita unicamente dalla funzione [`automated_field_value_extraction`](https://github.com/shini161/kibcat/blob/719635beb65b141d199cb4bcddb13a98250a57af/cat/plugins/kibcat/utils/generate_field_values.py#L10).

## Conversazione con CheshireCat
Inizialmente si è pensato all'utilizzo di un `@tool` del cat per poter raggiungere l'obiettivo, ma successivamente ci si è resi conto che esso non poteva andare bene in quanto implicava una conversazione **domanda → URL** diretta, che non era ciò che volevamo. 

Allora si è passati all'uso dei `@form`, i quali hanno una forma di conversazione meno ristretta e lasciano che l'utente possa avere una conversazione continua, e che possa fare delle correzioni, specificare ulteriormente la domana, o essere corretto a sua volta in caso di valori ambigui o non validi.

Il form normalmente è composto da una struttura leggermente diversa da quella che verrà elencata, perchè sono state apportate molte modifiche per rendere il form adatto all'obiettivo.

La struttura del form realizzata è composta da tre fasi principali:
- **Estrazione**: Durante la fase di estrazione la domanda dell'utente viene presa e tramite un prompt viene suddivisa in filtri. Per classificare le field da utilizzare nel prompt vengono anche passate le <a name="main_fields"></a>`main_fields`
- **Validazione**
- **Conferma** - invece che submit

## UI