from __future__ import annotations

from abc import ABC, abstractmethod

import wtflow


class DBServiceInterface(ABC):
    @abstractmethod
    def add_workflow(self, workflow: wtflow.Workflow) -> None:
        raise NotImplementedError

    @abstractmethod
    def start_execution(self, workflow: wtflow.Workflow, node: wtflow.Node) -> None:
        raise NotImplementedError

    @abstractmethod
    def end_execution(self, workflow: wtflow.Workflow, node: wtflow.Node, result: int | None = None) -> None:
        raise NotImplementedError


class NoDBService(DBServiceInterface):
    def add_workflow(self, workflow: wtflow.Workflow) -> None:
        pass

    def start_execution(self, workflow: wtflow.Workflow, node: wtflow.Node) -> None:
        pass

    def end_execution(self, workflow: wtflow.Workflow, node: wtflow.Node, result: int | None = None) -> None:
        pass
