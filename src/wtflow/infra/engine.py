from __future__ import annotations

import logging
import pathlib
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from typing import TYPE_CHECKING, Generator

from wtflow.config import Config
from wtflow.db.client import DBClient

if TYPE_CHECKING:
    from wtflow.infra.nodes import Node
    from wtflow.infra.workflow import Workflow

logger = logging.getLogger(__name__)


class Engine:
    def __init__(self, workflow: Workflow, config: Config | None = None, dry_run: bool = False) -> None:
        self.workflow = workflow
        self.config = config or Config.from_env()
        self.db = DBClient(self.config.db.url) if self.config.db.url else None
        self.dry_run = dry_run

    @contextmanager
    def _execute(self, node: Node) -> Generator[None, None, None]:
        if self.db:
            with self.db.Session() as session:
                self.db.start_execution(session, node)
                yield
                self.db.end_execution(session, node)
        else:
            yield

    def execute_node(self, node: Node, parallel: bool = False) -> int:
        logger.debug(f"Executing node {node.name!r}")
        failing_nodes = 0
        result = None
        with self._execute(node):
            if node.executable:
                result = node.executable.execute()
        if result and result.retcode != 0:
            logger.debug(f"Node {node.name!r} failed with return code {node.retcode}")
            failing_nodes += 1
        if not self.config.run.ignore_failure and failing_nodes > self.config.run.max_fail:
            return failing_nodes
        return failing_nodes + self.execute_children(node.parallel, node.children)

    def execute_children(self, parallel: bool, children: list[Node]) -> int:
        if parallel:
            logger.debug(f"Executing {', '.join(repr(child.name) for child in children)} children in parallel")
            with ThreadPoolExecutor() as pool:
                fs = [pool.submit(self.execute_node, child, parallel=True) for child in children]
                return sum(f.result() for f in fs)
        else:
            failing_nodes = 0
            for child in children:
                failing_nodes += self.execute_node(child)
                if not self.config.run.ignore_failure and failing_nodes > self.config.run.max_fail:
                    break
            return failing_nodes

    def run(self) -> int:
        if self.dry_run:
            self.workflow.print()
            return 0

        if self.db:
            with self.db.Session() as session:
                self.db.add_workflow(session, self.workflow)
                session.commit()
        self._set_artifact_paths(self.workflow.root)

        failing_nodes = self.execute_node(self.workflow.root)
        if failing_nodes:
            logger.error(f"Workflow failed with {failing_nodes} failing nodes.")
            return 1
        else:
            logger.info("Workflow completed successfully.")
            return 0

    @property
    def artifacts_dir(self) -> pathlib.Path | None:
        if not self.config.storage.artifacts_dir:
            return None

        return self.config.storage.artifacts_dir / self.workflow.id

    def _set_artifact_paths(self, node: Node, base_path: pathlib.Path | None = None) -> None:
        if not self.artifacts_dir:
            return

        if base_path is None:
            base_path = self.artifacts_dir

        node_path = base_path / node.id
        node_path.mkdir(parents=True)

        for artifact in node.artifacts:
            artifact.path = node_path / f"{artifact.name}"

        for child in node.children:
            if self.db:
                self._set_artifact_paths(child, self.artifacts_dir)
            else:
                self._set_artifact_paths(child, node_path)
