from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from dataclasses import asdict
from typing import TYPE_CHECKING, Generator

import yaml

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

    def execute_node(self, node: Node) -> int:
        logger.debug(f"Executing node {node.name!r}")
        failing_nodes = 0
        result = None
        with self._execute(node):
            if node.executable:
                result = node.executable.execute()
                node.result = result
        if result and result.retcode != 0:
            logger.debug(f"Node {node.name!r} failed with return code {result.retcode}")
            failing_nodes += 1
        if not self.config.run.ignore_failure and failing_nodes > 0:
            return failing_nodes
        return failing_nodes + self.execute_children(node.children, node.parallel)

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

        if self.db:
            with self.db.Session() as session:
                self.db.add_workflow(session, self.workflow)
                session.commit()

        failing_nodes = self.execute_node(self.workflow.root)
        if failing_nodes:
            logger.error(f"Workflow failed with {failing_nodes} failing nodes.")
            return 1
        else:
            logger.info("Workflow completed successfully.")
            return 0
