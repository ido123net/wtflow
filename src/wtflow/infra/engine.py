from __future__ import annotations

import logging

from wtflow.config import Config
from wtflow.infra.workflow import Workflow, WorkflowExecutor

logger = logging.getLogger(__name__)


class Engine:
    def __init__(self, config: Config | None = None) -> None:
        self.config = config or Config.from_ini()
        self.storage_service = self.config.storage.create_storage_service()
        self.db_service = self.config.database.create_db_service()
        self._workflow_execution: dict[int, WorkflowExecutor] = {}

    def run_workflow(self, workflow: Workflow) -> int:
        workflow_executor = WorkflowExecutor(workflow, self.storage_service, self.db_service)
        self._workflow_execution[id(workflow)] = workflow_executor

        failing_nodes = workflow_executor.run()
        if failing_nodes:
            logger.error(f"Workflow failed with {failing_nodes} failing nodes.")
            return 1
        else:
            logger.info("Workflow completed successfully.")
            return 0

    def get_workflow_executor(self, workflow: Workflow) -> WorkflowExecutor:
        return self._workflow_execution[id(workflow)]
