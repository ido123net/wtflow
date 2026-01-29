from __future__ import annotations

import logging

from wtflow.config import Config
from wtflow.infra.executors import NodeExecutor, NodeResult
from wtflow.infra.workflow import Workflow

logger = logging.getLogger(__name__)


class Engine:
    def __init__(self, config: Config | None = None) -> None:
        self.config = config or Config.from_ini()
        self.db_service = self.config.db_service
        self.storage_service = self.config.storage_service

    async def init_workflow(self, workflow: Workflow) -> int:
        return await self.db_service.add_workflow(workflow)

    async def run_workflow(self, workflow: Workflow) -> int:
        await self.db_service.create_tables()
        await self.init_workflow(workflow)
        result = await self.execute_workflow(workflow)
        await self.db_service.end_workflow(workflow, result)
        return result

    async def execute_workflow(self, workflow: Workflow) -> NodeResult:
        root_executor = NodeExecutor(workflow, workflow.root, self.storage_service, self.db_service)
        return await root_executor.execute()
