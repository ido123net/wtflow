from __future__ import annotations

import itertools
import logging
import os
import sys
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from typing import IO, TYPE_CHECKING, Any, Iterator

from wtflow.infra.executors import Executor, Result, get_executor
from wtflow.infra.nodes import Node

if TYPE_CHECKING:
    from wtflow.config import RunConfig
    from wtflow.db.service import DBServiceInterface
    from wtflow.infra.nodes import Node
    from wtflow.storage.service import StorageServiceInterface

if sys.version_info >= (3, 11):  # pragma: >=3.11 cover
    from typing import Self
else:  # pragma: <3.11 cover
    from typing_extensions import Self


logger = logging.getLogger(__name__)


@dataclass
class Workflow:
    name: str
    root: Node

    _id: int | None = field(default=None, repr=False, init=False)

    @property
    def nodes(self) -> list[Node]:
        return self._get_nodes(self.root)

    @property
    def id(self) -> str:
        _id = self._id or self.name
        return str(_id)

    def _get_nodes(self, node: Node) -> list[Node]:
        nodes = [node]
        for child in node.children:
            nodes.extend(self._get_nodes(child))
        return nodes

    def _init_node(self, node: Node, counter: Iterator[int]) -> None:
        node._lft = next(counter)
        for child in node.children:
            self._init_node(child, counter)
        node._rgt = next(counter)

    def __post_init__(self) -> None:
        counter = itertools.count(1)
        self._init_node(self.root, counter)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> Self:
        return cls(d["name"], root=Node.from_dict(d["root"]))

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "root": self.root.to_dict(),
        }


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

    def _read_stream(self, stream: IO[bytes], node: Node, artifact_name: str) -> bytes:
        res = b""
        for line in iter(stream.readline, b""):
            artifact = node.get_artifact(artifact_name)
            self.storage_service.append_to_artifact(artifact, self.workflow, node, line)
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
        with self.db_service.execute(self.workflow, node):
            executor = get_executor(node.executable)
            executor._execute(node.executable, stdout_tx, stderr_tx)
            os.close(stdout_tx)
            os.close(stderr_tx)
            node.result = self._wait_node(executor, node, stdout_rx, stderr_rx)

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
                if not self.run_config.ignore_failure and failing_nodes > 0:
                    break
            return failing_nodes
