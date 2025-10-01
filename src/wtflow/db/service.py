from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path

import wtflow


class DBServiceInterface(ABC):
    @abstractmethod
    def add_workflow(self, workflow: wtflow.Workflow) -> None:
        raise NotImplementedError

    @abstractmethod
    def start_execution(
        self,
        node: wtflow.Node,
        stdout_uri: str | None,
        stderr_uri: str | None,
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    def end_execution(self, node: wtflow.Node) -> None:
        raise NotImplementedError

    @contextmanager
    def execute(
        self,
        node: wtflow.Node,
        stdout: Path | None,
        stderr: Path | None,
    ) -> Generator[None, None, None]:
        stdout_uri = stdout.absolute().as_uri() if stdout else None
        stderr_uri = stderr.absolute().as_uri() if stderr else None
        self.start_execution(node, stdout_uri, stderr_uri)
        yield
        self.end_execution(node)


class NoDBService(DBServiceInterface):
    def add_workflow(self, workflow: wtflow.Workflow) -> None:
        pass

    def start_execution(
        self,
        node: wtflow.Node,
        stdout_uri: str | None,
        stderr_uri: str | None,
    ) -> None:
        pass

    def end_execution(self, node: wtflow.Node) -> None:
        pass
