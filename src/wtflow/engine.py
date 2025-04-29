from __future__ import annotations

import logging
import pathlib
from concurrent.futures import ThreadPoolExecutor
from typing import TYPE_CHECKING

from wtflow.config import Config
from wtflow.db.client import DBClient

if TYPE_CHECKING:
    from wtflow.nodes import Node
    from wtflow.workflow import Workflow

logger = logging.getLogger(__name__)


class Engine:
    def __init__(self, workflow: Workflow, stop_on_failure: bool = True):
        self.workflow = workflow
        self.conf = Config.load()
        self.db = DBClient(self.conf.db.url)
        with self.db.Session() as session:
            self.db.add_workflow(session, workflow)
            session.commit()
            for node in workflow.nodes:
                self._set_artifact_paths(node)

        self.stop_on_failure = stop_on_failure

    def execute_node(self, node: Node) -> int:
        failing_nodes = 0
        with self.db.Session() as session:
            self.db.start_execution(session, node)
            node.execute()
            self.db.end_execution(session, node)
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
    def artifacts_dir(self) -> pathlib.Path | None:
        if not self.conf.storage.artifacts_dir:
            return None

        return self.conf.storage.artifacts_dir / str(self.workflow.id)

    def _set_artifact_paths(self, node: Node) -> None:
        if not self.artifacts_dir:
            return

        node_path = self.artifacts_dir / str(node.id)

        for artifact in node.artifacts:
            artifact.path = node_path / f"{artifact.name}.{artifact.type.value}"
