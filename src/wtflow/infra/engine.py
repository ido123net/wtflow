from __future__ import annotations

import logging

from wtflow.config import Config
from wtflow.infra.executors import NodeExecutor
from wtflow.infra.workflow import Workflow

logger = logging.getLogger(__name__)


class Engine:
    def __init__(self, config: Config | None = None) -> None:
        self.config = config or Config.from_ini()
        self.storage_service = self.config.storage.create_storage_service()
        self.db_service = self.config.database.create_db_service()
        self.workflow_results: dict[int, int] = {}

    async def run_workflow(self, workflow: Workflow) -> int:
        await self.db_service.create_tables()
        await self.db_service.add_workflow(workflow)
        root_executor = NodeExecutor(workflow, workflow.root, self.storage_service, self.db_service)
        result = await root_executor.execute()
        self.workflow_results[id(workflow)] = result
        if result:
            return 1
        else:
            return 0
