# Style Guide
Per scrivere codice pulito, devi scrivere per gli altri prima che per la macchina.

---

## logger o BaseLogger
Se una funziona deve utilizzare dei `print`, tra i parametri si aggiunge un parametro **logger**
al quale si passa `BaseLogger`, all'interno della funzione verrà soltanto usato quello.
Fuori dalle funzioni, nei **global scope**, utilizzare direttamente `BaseLogger`.
Ciò rende facile capire se ci si trova in una funzione o no, e dà la possibilità di ignorare
facilmente i log nelle funzioni, basta non passare `BaseLogger`

```py
from typing import Type

from kiblog import BaseLogger


def example_func(logger: Type[BaseLogger] | None = None):
    if logger:
        logger.message("Using logger inside functions")

BaseLogger.message("Using BaseLogger outside functions")

if __name__ == "__main__":
    BaseLogger.message("BaseLogger here is also correct")

    # Calling the function - Logger ON
    example_func(logger=BaseLogger)
    
    # Calling the function - Logger OFF
    example_func()
```

## Parametri posizionali, quando?
```py
def example_func(param1: int, param2: str)
    # Some Core Logic...

# This is OK
example_func(
    param1 = "Hello",
    param2 = "Fire!"
)

# This is NOT OK
example_func("Hello", "Fire!")
```
