from __future__ import annotations

from wtflow.config import Config
from wtflow.infra.executors import NodeExecutor, NodeResult
from wtflow.infra.workflow import TreeWorkflow
from wtflow.services.servicer import Servicer


class Engine:
    def __init__(self, config: Config | None = None) -> None:
        self.config = config or Config()
        self.servicer = Servicer.from_config(self.config)

    async def run_workflow(self, workflow: TreeWorkflow) -> int:
        await self.servicer.db_service.add_workflow(workflow)
        result = await self.execute_workflow(workflow)
        await self.servicer.db_service.end_workflow(workflow, result)
        return result

    async def execute_workflow(self, workflow: TreeWorkflow) -> NodeResult:
        root_executor = NodeExecutor(workflow, workflow.root, self.servicer)
        return await root_executor.execute()
