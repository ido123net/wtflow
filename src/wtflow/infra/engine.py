from __future__ import annotations

import logging

import yaml

from wtflow.config import Config
from wtflow.infra.workflow import Workflow, WorkflowExecutor

logger = logging.getLogger(__name__)


class Engine:
    def __init__(self, config: Config | None = None) -> None:
        self.config = config or Config.from_ini()
        self.storage_service = self.config.storage.create_storage_service()
        self.db_service = self.config.database.create_db_service()

    def run_workflow(self, workflow: Workflow, *, dry_run: bool = False) -> int:
        if dry_run:
            print(yaml.dump(workflow.to_dict(), indent=2, sort_keys=False), end="")
            return 0

        self.db_service.add_workflow(workflow)
        workflow_executor = WorkflowExecutor(workflow, self.storage_service, self.db_service, self.config.run)

        failing_nodes = workflow_executor.run()
        if failing_nodes:
            logger.error(f"Workflow failed with {failing_nodes} failing nodes.")
            return 1
        else:
            logger.info("Workflow completed successfully.")
            return 0
