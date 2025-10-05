from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Callable, Type

if TYPE_CHECKING:
    from wtflow.infra.executors import Executor


@dataclass
class Executable(ABC):
    timeout: float | None = field(default=None, kw_only=True)

    @classmethod
    @abstractmethod
    def get_executor(cls) -> Type[Executor]: ...


@dataclass
class PyFunc(Executable):
    func: Callable[..., Any]
    args: tuple[Any, ...] = field(default_factory=tuple, kw_only=True)
    kwargs: dict[str, Any] = field(default_factory=dict, kw_only=True)

    @classmethod
    def get_executor(cls) -> Type[Executor]:
        from wtflow.infra.executors import MultiprocessingExecutor

        return MultiprocessingExecutor


@dataclass
class Command(Executable):
    cmd: str

    @classmethod
    def get_executor(cls) -> Type[Executor]:
        from wtflow.infra.executors import SubprocessExecutor

        return SubprocessExecutor
