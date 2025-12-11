from __future__ import annotations

import sys
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Callable, Type

if sys.version_info >= (3, 11):  # pragma: >=3.11 cover
    from typing import Self
else:  # pragma: <3.11 cover
    from typing_extensions import Self

if TYPE_CHECKING:
    from wtflow.infra.executors import Executor


@dataclass
class Executable(ABC):
    timeout: float | None = field(default=None, kw_only=True)

    @classmethod
    @abstractmethod
    def get_executor(cls) -> Type[Executor]: ...

    @abstractmethod
    def to_dict(self) -> dict[str, Any]: ...


@dataclass
class PyFunc(Executable):
    func: Callable[..., Any]
    args: tuple[Any, ...] = field(default_factory=tuple, kw_only=True)
    kwargs: dict[str, Any] = field(default_factory=dict, kw_only=True)

    @classmethod
    def get_executor(cls) -> Type[Executor]:
        from wtflow.infra.executors import MultiprocessingExecutor

        return MultiprocessingExecutor

    def to_dict(self) -> dict[str, Any]:
        args = [str(arg) for arg in self.args]
        kwargs = [f"--{key} {str(value)}" for key, value in self.kwargs.items()]
        cmd = f"wtfunc {self.func.__module__}.{self.func.__name__}"
        if args:
            cmd = f"{cmd} {' '.join(args)}"
        if kwargs:
            cmd = f"{cmd} {' '.join(kwargs)}"
        return {"cmd": cmd}


@dataclass
class Command(Executable):
    cmd: str

    @classmethod
    def get_executor(cls) -> Type[Executor]:
        from wtflow.infra.executors import SubprocessExecutor

        return SubprocessExecutor

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> Self:
        return cls(**d)

    def to_dict(self) -> dict[str, Any]:
        return {"cmd": self.cmd}
