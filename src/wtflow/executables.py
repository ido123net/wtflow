from enum import StrEnum, auto
from typing import Annotated, Any, Callable, Literal

from pydantic import BaseModel, BeforeValidator, field_serializer

from wtflow.utils import load_func


class ExecutalbeType(StrEnum):
    COMMAND = auto()
    PY_FUNC = auto()


class Executable(BaseModel):
    type: ExecutalbeType


class Command(Executable):
    type: Literal[ExecutalbeType.COMMAND] = ExecutalbeType.COMMAND
    cmd: str


def _func_path(value: Callable[..., Any]) -> str:
    return f"{value.__module__}.{value.__name__}"


class PyFunc(Executable):
    type: Literal[ExecutalbeType.PY_FUNC] = ExecutalbeType.PY_FUNC
    func: Annotated[Callable[..., Any] | str, BeforeValidator(load_func)]
    args: tuple[Any, ...] = ()
    kwargs: dict[str, Any] = {}

    @field_serializer("func", when_used="json")
    def serialize_func(self, value: Callable[..., Any]) -> str:
        return _func_path(value)

    def __str__(self) -> str:
        args = ", ".join(repr(arg) for arg in self.args)
        kwargs = ", ".join(f"{k}={v!r}" for k, v in self.kwargs.items())
        assert not isinstance(self.func, str)
        return f"{_func_path(self.func)}({args}, {kwargs})"
