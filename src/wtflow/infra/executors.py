from __future__ import annotations

import asyncio
import logging
from enum import IntEnum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from wtflow.infra.nodes import Node
    from wtflow.infra.workflow import Workflow
    from wtflow.services.db.service import DBServiceInterface
    from wtflow.services.storage.service import StorageServiceInterface


logger = logging.getLogger(__name__)


class NodeResult(IntEnum):
    SUCESS = 0
    FAIL = 1
    CHILD_FAILED = 2
    TIMEOUT = 3
    CANCEL = 4


class NodeExecutor:
    def __init__(
        self,
        workflow: Workflow,
        node: Node,
        storage_service: StorageServiceInterface,
        db_service: DBServiceInterface,
    ) -> None:
        self.workflow = workflow
        self.node = node
        self.storage_service = storage_service
        self.db_service = db_service
        self.process: asyncio.subprocess.Process | None = None

    async def execute(self) -> NodeResult:
        logger.debug(f"Start execution of {self.node.name!r}")
        await self.db_service.start_execution(self.workflow, self.node)
        try:
            return await self._execute()
        finally:
            retcode = await self.process.wait() if self.process else None
            logger.debug(f"Node {self.node.name!r} {retcode = }")
            await self.db_service.end_execution(self.workflow, self.node, retcode)

    async def _execute(self) -> NodeResult:
        command = self.node.command

        if command is None:
            return await self.execute_children()

        with (
            self.storage_service.open_artifact(self.workflow, self.node, "stdout") as stdout,
            self.storage_service.open_artifact(self.workflow, self.node, "stderr") as stderr,
        ):
            self.process = await asyncio.create_subprocess_shell(
                command,
                shell=True,
                stdout=stdout,
                stderr=stderr,
            )
            try:
                result = await asyncio.wait_for(self.process.wait(), self.node.timeout)
                if result:
                    return NodeResult.FAIL
            except asyncio.TimeoutError:
                logger.debug(f"Node {self.node.name} timeout")
                return NodeResult.TIMEOUT
            except asyncio.CancelledError:
                logger.debug(f"Node {self.node.name} cancel")
                return NodeResult.CANCEL
            finally:
                if self.process.returncode is None:
                    self.process.terminate()

        return await self.execute_children()

    async def execute_children(self) -> NodeResult:
        try:
            return await self._execute_children()
        except asyncio.CancelledError:
            return NodeResult.CHILD_FAILED

    async def _execute_children(self) -> NodeResult:
        children = self.node.children
        parallel = self.node.parallel
        executors = [type(self)(self.workflow, child, self.storage_service, self.db_service) for child in children]
        if parallel:
            logger.debug(f"Executing {', '.join(repr(child.name) for child in children)} children in parallel")
            tasks = [asyncio.create_task(executor._execute()) for executor in executors]
            for result in asyncio.as_completed(tasks):
                if await result:
                    raise asyncio.CancelledError
        else:
            for executor in executors:
                if await executor._execute():
                    raise asyncio.CancelledError
        return NodeResult.SUCESS
