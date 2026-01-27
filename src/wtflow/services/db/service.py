from __future__ import annotations

from abc import ABC, abstractmethod

import wtflow


class DBServiceInterface(ABC):
    @abstractmethod
    async def create_tables(self) -> None:
        raise NotImplementedError

    @abstractmethod
    async def add_workflow(self, workflow: wtflow.Workflow) -> None:
        raise NotImplementedError

    @abstractmethod
    async def start_execution(self, workflow: wtflow.Workflow, node: wtflow.Node) -> None:
        raise NotImplementedError

    @abstractmethod
    async def end_execution(self, workflow: wtflow.Workflow, node: wtflow.Node, result: int | None = None) -> None:
        raise NotImplementedError


class NoDBService(DBServiceInterface):
    async def create_tables(self) -> None:
        pass

    async def add_workflow(self, workflow: wtflow.Workflow) -> None:
        pass

    async def start_execution(self, workflow: wtflow.Workflow, node: wtflow.Node) -> None:
        pass

    async def end_execution(self, workflow: wtflow.Workflow, node: wtflow.Node, result: int | None = None) -> None:
        pass
