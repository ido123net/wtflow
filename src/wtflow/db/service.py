from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Generator
from contextlib import contextmanager

import wtflow


class DBServiceInterface(ABC):
    @abstractmethod
    def add_workflow(self, workflow: wtflow.Workflow) -> None:
        raise NotImplementedError

    @abstractmethod
    def start_execution(self, node: wtflow.Node) -> None:
        raise NotImplementedError

    @abstractmethod
    def end_execution(self, node: wtflow.Node) -> None:
        raise NotImplementedError

    @contextmanager
    def execute(self, node: wtflow.Node) -> Generator[None, None, None]:
        self.start_execution(node)
        yield
        self.end_execution(node)


class NoDBService(DBServiceInterface):
    def add_workflow(self, workflow: wtflow.Workflow) -> None:
        pass

    def start_execution(self, node: wtflow.Node) -> None:
        pass

    def end_execution(self, node: wtflow.Node) -> None:
        pass
