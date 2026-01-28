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
        self.workflow_results: dict[int, Workflow] = {}

    async def init_workflow(self, workflow: Workflow) -> int:
        workflow_id = await self.db_service.add_workflow(workflow)
        self.workflow_results[workflow_id] = workflow
        return workflow_id

    async def run_workflow(self, workflow: Workflow) -> int:
        await self.db_service.create_tables()
        workflow_id = await self.init_workflow(workflow)
        return await self.execute_workflow(workflow_id)

    async def execute_workflow(self, workflow_id: int) -> NodeResult:
        workflow = self.workflow_results.pop(workflow_id)
        root_executor = NodeExecutor(workflow, workflow.root, self.storage_service, self.db_service)
        return await root_executor.execute()
