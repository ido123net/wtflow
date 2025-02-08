from typing import Any, Callable


def load_func(value: Callable[..., Any] | str) -> Callable[..., Any]:
    if isinstance(value, str):
        module_name, func_name = value.rsplit(".", 1)
        module = __import__(module_name, fromlist=[func_name])
        value = getattr(module, func_name)
    assert callable(value)
    return value
