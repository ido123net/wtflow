from __future__ import annotations

from abc import abstractmethod

import wtflow
from wtflow.infra.info import ExecutionInfo, RunInfo
from wtflow.services.base_service import BaseService


class DBService(BaseService):
    @abstractmethod
    async def save_graph(self, graph: wtflow.Graph) -> None:
        raise NotImplementedError

    @abstractmethod
    async def update_run_info(self, run_info: RunInfo) -> None:
        raise NotImplementedError

    @abstractmethod
    async def update_execution_info(self, execution_info: ExecutionInfo) -> None:
        raise NotImplementedError


class NoDBService(DBService):
    async def save_graph(self, graph: wtflow.Graph) -> None:
        pass

    async def update_run_info(self, run_info: RunInfo) -> None:
        pass

    async def update_execution_info(self, execution_info: ExecutionInfo) -> None:
        pass
