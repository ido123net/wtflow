from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from wtflow.nodes import Node
    from wtflow.workflow import Workflow

logger = logging.getLogger(__name__)


class Engine:
    def __init__(self, workflow: Workflow, stop_on_failure: bool = True):
        self.workflow = workflow
        self.stop_on_failure = stop_on_failure

    def execute_node(self, node: Node) -> int:
        failing_nodes = 0
        node.execute()
        if node.result and node.result.returncode != 0:
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
