from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from functools import cached_property
from typing import TYPE_CHECKING, Any, Callable

from wtflow.infra.executors import Executor, MultiprocessingExecutor, Result, SubprocessExecutor

if TYPE_CHECKING:
    from wtflow.infra.nodes import Node


@dataclass
class Executable(ABC):
    timeout: float | None = field(default=None, kw_only=True)

    @abstractmethod
    def get_executor(self) -> Executor:
        """Return the executor for the executable."""

    @cached_property
    def executor(self) -> Executor:
        return self.get_executor()

    def set_node(self, node: Node) -> None:
        self._node = node

    @property
    def node(self) -> Node | None:
        try:
            return self._node
        except AttributeError:
            return None

    def execute(self) -> Result:
        self.executor.execute(self)
        return self.executor._wait(self)


@dataclass
class PyFunc(Executable):
    func: Callable[..., Any]
    args: tuple[Any, ...] = field(default_factory=tuple, kw_only=True)
    kwargs: dict[str, Any] = field(default_factory=dict, kw_only=True)

    def get_executor(self) -> Executor:
        return MultiprocessingExecutor(self)

    def __repr__(self) -> str:
        module = self.func.__module__
        name = self.func.__name__
        return f"{self.__class__.__name__}(<{module}.{name}>)"


@dataclass
class Command(Executable):
    cmd: str

    def get_executor(self) -> Executor:
        return SubprocessExecutor(self)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(cmd={self.cmd!r})"
