from __future__ import annotations

import itertools
import logging
from concurrent.futures import ThreadPoolExecutor
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel

from wtflow.infra.executors import Executor
from wtflow.infra.nodes import Node

if TYPE_CHECKING:
    from wtflow.infra.nodes import Node
    from wtflow.services.db.service import DBServiceInterface
    from wtflow.services.storage.service import StorageServiceInterface

logger = logging.getLogger(__name__)


class Workflow(BaseModel):
    name: str
    root: Node

    _id: int | None = None

    @property
    def id(self) -> int | str:
        return self._id if self._id else self.name

    @id.setter
    def id(self, value: int) -> None:
        self._id = value

    def model_post_init(self, context: Any, /) -> None:
        counter = itertools.count(1)
        self.root.set_lft_rgt(counter)


class WorkflowExecutor:
    def __init__(
        self,
        workflow: Workflow,
        storage_service: StorageServiceInterface,
        db_service: DBServiceInterface,
    ):
        self.workflow = workflow
        self.storage_service = storage_service
        self.db_service = db_service
        self._node_result: dict[int, int | None] = {}

    def run(self) -> int:
        self.db_service.add_workflow(self.workflow)
        return self.execute_node(self.workflow.root)

    def execute_node(self, node: Node) -> int:
        if not node.command:
            return self.execute_children(node.children, node.parallel)

        logger.debug(f"Executing node {node.name!r}")
        self.db_service.start_execution(self.workflow, node)
        with (
            self.storage_service.open_artifact(self.workflow, node, "stdout") as stdout,
            self.storage_service.open_artifact(self.workflow, node, "stderr") as stderr,
        ):
            executor = Executor(node.command, node.timeout, stdout, stderr)
            result = executor.execute()
        self._node_result[id(node)] = result
        self.db_service.end_execution(self.workflow, node, result)

        fail = result != 0

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
            for child in children:
                if self.execute_node(child):
                    return 1
            return 0

    def node_result(self, node: Node) -> int | None:
        return self._node_result.get(id(node))
