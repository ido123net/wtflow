from __future__ import annotations

import pathlib
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from functools import cached_property
from typing import Any, Callable

from wtflow.infra.executors import Executor, MultiprocessingExecutor, Result, SubprocessExecutor


@dataclass
class Executable(ABC):
    timeout: float | None = field(default=None, kw_only=True)

    @abstractmethod
    def get_executor(self) -> Executor:
        """Return the executor for the executable."""

    @cached_property
    def executor(self) -> Executor:
        return self.get_executor()

    def execute(self, stdout: pathlib.Path | None = None, stderr: pathlib.Path | None = None) -> Result:
        self.executor.execute(self)
        return self.executor.wait(self, stdout, stderr)


@dataclass
class PyFunc(Executable):
    func: Callable[..., Any]
    args: tuple[Any, ...] = field(default_factory=tuple, kw_only=True)
    kwargs: dict[str, Any] = field(default_factory=dict, kw_only=True)

    def get_executor(self) -> Executor:
        return MultiprocessingExecutor(self)


@dataclass
class Command(Executable):
    cmd: str

    def get_executor(self) -> Executor:
        return SubprocessExecutor(self)
