import time
from typing import Any, Callable, TypeVar

T = TypeVar("T")


def time_ms(func: Callable[..., T], *args: Any, **kwargs: Any) -> tuple[T, float]:
    """
    Measures the execution time of a function in milliseconds.

    Args:
        func: The function to time
        *args: Positional arguments to pass to the function
        **kwargs: Keyword arguments to pass to the function

    Returns:
        tuple: (result of the function call, execution time in milliseconds)
    """
    start = time.perf_counter()
    result = func(*args, **kwargs)
    end = time.perf_counter()
    execution_time_ms = (end - start) * 1000

    return result, execution_time_ms
