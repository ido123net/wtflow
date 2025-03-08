from abc import ABC, abstractmethod
from typing import Any, Callable, ParamSpec, TypeVar

from wtflow.executors import Executor, MultiprocessingExecutor, Result, SubprocessExecutor

P = ParamSpec("P")
R = TypeVar("R")


class Executable(ABC):
    """Base class for an executable object."""

    def __init__(self, timeout: float | None = None) -> None:
        self.timeout = timeout

    @abstractmethod
    def get_executor(self) -> Executor:
        """Return the executor for the executable."""

    def run(self) -> Result:
        executor = self.get_executor()
        executor.execute()
        return Result(
            returncode=executor.returncode,
            stdout=executor.stdout,
            stderr=executor.stderr,
        )


class PyFunc(Executable):
    """Represents a Python function as an executable object."""

    def __init__(
        self,
        func: Callable[..., Any],
        *,
        timeout: float | None = None,
        args: tuple[Any, ...] = (),
        kwargs: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(timeout)
        self.func = func
        self.args = args
        self.kwargs: dict[str, Any] = kwargs or {}

    def get_executor(self) -> Executor:
        return MultiprocessingExecutor(self)

    def __repr__(self) -> str:
        func_path = f"{self.func.__module__}.{self.func.__name__}"
        return f"{self.__class__.__name__}(target={func_path}, args={self.args!r}, kwargs={self.kwargs!r})"


class Command(Executable):
    """Represents an external command as an executable object."""

    def __init__(
        self,
        cmd: str,
        timeout: float | None = None,
    ) -> None:
        super().__init__(timeout)
        self.cmd = cmd

    def get_executor(self) -> Executor:
        return SubprocessExecutor(self)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(cmd={self.cmd!r})"
