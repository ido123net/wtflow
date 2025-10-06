from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Generator
from contextlib import contextmanager

import wtflow
from wtflow.storage.service import StorageServiceInterface


class DBServiceInterface(ABC):
    def __init__(self, storage_service: StorageServiceInterface) -> None:
        self.storage_service = storage_service

    @abstractmethod
    def add_workflow(self, workflow: wtflow.Workflow) -> None:
        raise NotImplementedError

    @abstractmethod
    def start_execution(self, workflow: wtflow.Workflow, node: wtflow.Node) -> None:
        raise NotImplementedError

    @abstractmethod
    def end_execution(self, workflow: wtflow.Workflow, node: wtflow.Node) -> None:
        raise NotImplementedError

    @contextmanager
    def execute(self, workflow: wtflow.Workflow, node: wtflow.Node) -> Generator[None, None, None]:
        self.start_execution(workflow, node)
        yield
        self.end_execution(workflow, node)


class NoDBService(DBServiceInterface):
    def add_workflow(self, workflow: wtflow.Workflow) -> None:
        pass

    def start_execution(self, workflow: wtflow.Workflow, node: wtflow.Node) -> None:
        pass

    def end_execution(self, workflow: wtflow.Workflow, node: wtflow.Node) -> None:
        pass
