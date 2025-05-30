from typing import Any, Callable, List, TypeVar

T = TypeVar("T", bound=Callable[..., Any])

class mark:
    def parametrize(self, argnames: str, argvalues: List[Any]) -> Callable[[T], T]: ...

mark_instance: mark  # or _mark: mark
