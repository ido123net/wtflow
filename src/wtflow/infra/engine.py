from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict
from typing import TYPE_CHECKING

import yaml

from wtflow.config import Config
from wtflow.db.service import NoDBService
from wtflow.storage.service import NoStorageService

if TYPE_CHECKING:
    from wtflow.infra.nodes import Node
    from wtflow.infra.workflow import Workflow

logger = logging.getLogger(__name__)


class Engine:
    def __init__(self, workflow: Workflow, config: Config | None = None, dry_run: bool = False) -> None:
        self.workflow = workflow
        self.config = config or Config.from_ini()
        self.db_service = self.config.database.create_db_service() if self.config.database else NoDBService()
        self.storage_service = (
            self.config.storage.create_storage_service() if self.config.storage else NoStorageService()
        )
        self.dry_run = dry_run

    def execute_node(self, node: Node) -> int:
        if not node.executable:
            return self.execute_children(node.children, node.parallel)

        logger.debug(f"Executing node {node.name!r}")
        stdout, stderr = self.storage_service.create_node_logs(self.workflow, node)
        with self.db_service.execute(node, stdout, stderr):
            node.result = node.executable.execute(stdout=stdout, stderr=stderr)

        if node.fail:
            return 1

        return int(node.fail) + self.execute_children(node.children, node.parallel)

    def execute_children(self, children: list[Node], parallel: bool) -> int:
        if parallel:
            logger.debug(f"Executing {', '.join(repr(child.name) for child in children)} children in parallel")
            with ThreadPoolExecutor() as pool:
                fs = [pool.submit(self.execute_node, child) for child in children]
                return sum(f.result() for f in fs)
        else:
            failing_nodes = 0
            for child in children:
                failing_nodes += self.execute_node(child)
                if not self.config.run.ignore_failure and failing_nodes > 0:
                    break
            return failing_nodes

    def run(self) -> int:
        if self.dry_run:
            flow_dict = asdict(
                self.workflow, dict_factory=lambda x: {k: v for k, v in x if not k.startswith("_") and bool(v)}
            )
            print(yaml.dump(flow_dict, indent=2, sort_keys=False), end="")
            return 0

        self.db_service.add_workflow(self.workflow)

        failing_nodes = self.execute_node(self.workflow.root)
        if failing_nodes:
            logger.error(f"Workflow failed with {failing_nodes} failing nodes.")
            return 1
        else:
            logger.info("Workflow completed successfully.")
            return 0
