from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict
from typing import IO, TYPE_CHECKING

import yaml

from wtflow.config import Config
from wtflow.infra.executors import Executor, Result, get_executor

if TYPE_CHECKING:
    from wtflow.infra.nodes import Node
    from wtflow.infra.workflow import Workflow

logger = logging.getLogger(__name__)


class Engine:
    def __init__(self, workflow: Workflow, config: Config | None = None, dry_run: bool = False) -> None:
        self.workflow = workflow
        self.config = config or Config.from_ini()
        self.storage_service = self.config.storage.create_storage_service()
        self.db_service = self.config.database.create_db_service(self.storage_service)
        self.dry_run = dry_run

    def _read_stream(self, stream: IO[bytes], node: Node, artifact_name: str) -> bytes:
        res = b""
        for line in iter(stream.readline, b""):
            artifact = node.get_artifact(artifact_name)
            self.storage_service.append_to_artifact(artifact, self.workflow, node, line)
            res += line
        return res

    def _wait_node(self, executor: Executor, node: Node) -> Result:
        assert executor.stdout is not None
        assert executor.stderr is not None
        assert node.executable
        with ThreadPoolExecutor(max_workers=3) as pool:
            _retcode_f = pool.submit(executor._wait, node.executable)
            _stdout_f = pool.submit(self._read_stream, executor.stdout, node, "stdout")
            _stderr_f = pool.submit(self._read_stream, executor.stderr, node, "stderr")

        return Result(
            retcode=_retcode_f.result(),
            stdout=_stdout_f.result(),
            stderr=_stderr_f.result(),
        )

    def execute_node(self, node: Node) -> int:
        if not node.executable:
            return self.execute_children(node.children, node.parallel)

        logger.debug(f"Executing node {node.name!r}")
        with self.db_service.execute(self.workflow, node):
            executor = get_executor(node.executable)
            executor._execute(node.executable)
            node.result = self._wait_node(executor, node)

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
