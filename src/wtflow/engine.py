from __future__ import annotations

import logging
import pathlib
from concurrent.futures import ThreadPoolExecutor
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from wtflow.nodes import Node
    from wtflow.workflow import Workflow

logger = logging.getLogger(__name__)

LOGS_DIR = pathlib.Path("logs")


class Engine:
    def __init__(self, workflow: Workflow, stop_on_failure: bool = True):
        self.workflow = workflow
        self._set_artifact_paths(self.workflow)
        self.stop_on_failure = stop_on_failure

    def execute_node(self, node: Node) -> int:
        failing_nodes = 0
        node.execute()
        if node.retcode and node.retcode != 0:
            failing_nodes += 1
        if self.stop_on_failure and failing_nodes:
            return failing_nodes
        return failing_nodes + self.execute_children(node.parallel, node.children)

    def execute_children(self, parallel: bool, children: list[Node]) -> int:
        if parallel:
            with ThreadPoolExecutor() as pool:
                return sum(pool.map(self.execute_node, children))
        else:
            failing_nodes = 0
            for child in children:
                failing_nodes += self.execute_node(child)
                if self.stop_on_failure and failing_nodes:
                    return failing_nodes
            return failing_nodes

    def run(self) -> int:
        failing_nodes = self.execute_node(self.workflow.root)
        if failing_nodes:
            logger.error(f"Workflow failed with {failing_nodes} failing nodes.")
            return 1
        else:
            logger.info("Workflow completed successfully.")
            return 0

    def _set_artifact_paths(self, workflow: Workflow) -> None:
        logger.debug(f"Setting artifact paths for workflow: {workflow.id}")
        for node in workflow.nodes:
            for artifact in node.artifacts:
                if artifact.file_path is not None:
                    continue
                artifact.path = LOGS_DIR / workflow.id / node.id / f"{artifact.name}.{artifact.type.value}"
                artifact.path.parent.mkdir(parents=True, exist_ok=True)
                logger.debug(f"Set artifact path: {artifact.path}")
