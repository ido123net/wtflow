from __future__ import annotations

from abc import abstractmethod

import wtflow
from wtflow.services.base_service import BaseService


class DBServiceInterface(BaseService):
    @abstractmethod
    async def add_workflow(self, workflow: wtflow.TreeWorkflow) -> None:
        raise NotImplementedError

    @abstractmethod
    async def end_workflow(self, workflow: wtflow.TreeWorkflow, result: int) -> None:
        raise NotImplementedError

    @abstractmethod
    async def start_execution(self, workflow: wtflow.TreeWorkflow, node: wtflow.TreeNode) -> None:
        raise NotImplementedError

    @abstractmethod
    async def end_execution(
        self, workflow: wtflow.TreeWorkflow, node: wtflow.TreeNode, result: int | None = None
    ) -> None:
        raise NotImplementedError


class NoDBService(DBServiceInterface):
    async def add_workflow(self, workflow: wtflow.TreeWorkflow) -> None:
        pass

    async def start_execution(self, workflow: wtflow.TreeWorkflow, node: wtflow.TreeNode) -> None:
        pass

    async def end_execution(
        self, workflow: wtflow.TreeWorkflow, node: wtflow.TreeNode, result: int | None = None
    ) -> None:
        pass

    async def end_workflow(self, workflow: wtflow.TreeWorkflow, result: int) -> None:
        pass
