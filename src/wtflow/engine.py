from __future__ import annotations

import logging
import pathlib
from concurrent.futures import ThreadPoolExecutor
from typing import TYPE_CHECKING

from wtflow.db import DB

if TYPE_CHECKING:
    from wtflow.nodes import Node
    from wtflow.workflow import Workflow

logger = logging.getLogger(__name__)

LOGS_DIR = pathlib.Path("logs")


class Engine:
    def __init__(self, workflow: Workflow, stop_on_failure: bool = True):
        self.workflow = workflow
        self.db = DB()
        self.db.insert_workflow(workflow)

        self._set_artifact_paths(self.workflow, self.workflow.root)
        self.stop_on_failure = stop_on_failure

    def execute_node(self, node: Node) -> int:
        failing_nodes = 0
        node.execute()
        self.db.update_node(node)
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

    @property
    def logs_dir(self) -> pathlib.Path:
        return LOGS_DIR / str(self.workflow.id)

    def _set_artifact_paths(self, workflow: Workflow, node: Node) -> None:
        _node_path = str(node.name)
        _node_ptr = node
        while _node_ptr.parent:
            _node_path = f"{_node_ptr.parent.name}/{_node_path}"
            _node_ptr = _node_ptr.parent

        node_path = self.logs_dir / _node_path
        node_path.mkdir(parents=True, exist_ok=True)

        for artifact in node.artifacts:
            if artifact.file_path is not None:
                continue
            artifact.path = node_path / f"{artifact.name}.{artifact.type.value}"
        self.db.add_artifacts(node)
        for child in node.children:
            self._set_artifact_paths(workflow, child)
