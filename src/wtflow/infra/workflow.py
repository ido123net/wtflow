from __future__ import annotations

import logging
import os
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from typing import IO, TYPE_CHECKING
from uuid import uuid4

from wtflow.infra.executors import Executor, Result
from wtflow.infra.nodes import Node

if TYPE_CHECKING:
    from wtflow.config import RunConfig
    from wtflow.infra.nodes import Node
    from wtflow.services.db.service import DBServiceInterface
    from wtflow.services.storage.service import StorageServiceInterface

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Workflow:
    name: str
    root: Node

    id: str = field(default_factory=lambda: uuid4().hex, repr=False, init=False)


class WorkflowExecutor:
    def __init__(
        self,
        workflow: Workflow,
        storage_service: StorageServiceInterface,
        db_service: DBServiceInterface,
        run_config: RunConfig,
    ):
        self.workflow = workflow
        self.storage_service = storage_service
        self.db_service = db_service
        self.run_config = run_config
        self._node_result: dict[Node, Result | None] = defaultdict(lambda: None)

    def _read_stream(self, stream: IO[bytes], node: Node, stream_name: str) -> bytes:
        res = b""
        for line in iter(stream.readline, b""):
            self.storage_service.append_to_artifact(self.workflow, node, stream_name, line)
            res += line
        stream.close()
        return res

    def _wait_node(self, executor: Executor, node: Node, stdout_fd: int, stderr_fd: int) -> Result:
        assert node.executable
        stdout = os.fdopen(stdout_fd, "rb")
        stderr = os.fdopen(stderr_fd, "rb")
        with ThreadPoolExecutor(max_workers=3) as pool:
            _retcode_f = pool.submit(executor._wait, node.executable)
            _stdout_f = pool.submit(self._read_stream, stdout, node, "stdout")
            _stderr_f = pool.submit(self._read_stream, stderr, node, "stderr")

        return Result(
            retcode=_retcode_f.result(),
            stdout=_stdout_f.result(),
            stderr=_stderr_f.result(),
        )

    def run(self) -> int:
        return self.execute_node(self.workflow.root)

    def execute_node(self, node: Node) -> int:
        if not node.executable:
            return self.execute_children(node.children, node.parallel)

        stdout_rx, stdout_tx = os.pipe()
        stderr_rx, stderr_tx = os.pipe()

        logger.debug(f"Executing node {node.name!r}")
        self.db_service.start_execution(self.workflow, node)
        executor = Executor(node.executable)
        executor._execute(node.executable, stdout_tx, stderr_tx)
        os.close(stdout_tx)
        os.close(stderr_tx)
        result = self._wait_node(executor, node, stdout_rx, stderr_rx)
        self._node_result[node] = result
        self.db_service.end_execution(self.workflow, node, result)

        fail = result.retcode != 0

        if fail:
            return 1

        return int(fail) + self.execute_children(node.children, node.parallel)

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
                if not self.run_config.ignore_failure and failing_nodes > 0:
                    break
            return failing_nodes

    def node_result(self, node: Node) -> Result | None:
        return self._node_result[node]
