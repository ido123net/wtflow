from __future__ import annotations

from abc import abstractmethod

import wtflow
from wtflow.services.base_service import BaseService


class DBServiceInterface(BaseService):
    @abstractmethod
    async def create_tables(self) -> None:
        raise NotImplementedError

    @abstractmethod
    async def add_workflow(self, workflow: wtflow.Workflow) -> int:
        raise NotImplementedError

    @abstractmethod
    async def end_workflow(self, workflow: wtflow.Workflow, result: int) -> None:
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

    async def add_workflow(self, workflow: wtflow.Workflow) -> int:
        return id(workflow)

    async def start_execution(self, workflow: wtflow.Workflow, node: wtflow.Node) -> None:
        pass

    async def end_execution(self, workflow: wtflow.Workflow, node: wtflow.Node, result: int | None = None) -> None:
        pass

    async def end_workflow(self, workflow: wtflow.Workflow, result: int) -> None:
        pass
