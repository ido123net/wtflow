from __future__ import annotations

import asyncio
import logging
import os
import signal
from enum import IntEnum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from wtflow.infra.nodes import Node
    from wtflow.infra.workflow import Workflow
    from wtflow.services.servicer import Servicer

logger = logging.getLogger(__name__)


class NodeResult(IntEnum):
    SUCCESS = 0
    FAIL = 1
    CHILD_FAILED = 2
    TIMEOUT = 3
    CANCEL = 4


class NodeExecutor:
    def __init__(
        self,
        workflow: Workflow,
        node: Node,
        servicer: Servicer,
    ) -> None:
        self.workflow = workflow
        self.node = node
        self.servicer = servicer
        self._process: asyncio.subprocess.Process | None = None

    async def execute(self) -> NodeResult:
        logger.debug(f"Start execution of {self.node.name!r}")
        await self.servicer.db_service.start_execution(self.workflow, self.node)
        result = await self._execute_command(self.node.command) or await self._execute_children()
        logger.debug(f"End execution of {self.node.name!r}")
        logger.debug(f"Node {self.node.name!r} {result = }")
        await self.servicer.db_service.end_execution(self.workflow, self.node, result)
        return result

    async def _read_stream(self, name: str) -> None:
        assert self._process is not None
        stream: asyncio.StreamReader = getattr(self._process, name)
        with self.servicer.storage_service.open_artifact(self.workflow, self.node, name) as f:
            while data := await stream.readline():
                logger.debug(f"got data: {data=}")
                f.write(data)

    def _terminate(self) -> None:
        if self._process and self._process.returncode is None:
            logger.debug("Terminate process")
            os.killpg(os.getpgid(self._process.pid), signal.SIGTERM)

    async def _execute_command(self, command: str | None) -> NodeResult:
        if command is None:
            return NodeResult.SUCCESS

        self._process = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            start_new_session=True,
        )
        pid = self._process.pid
        logger.debug(f"started process with {pid=}")
        stdout_task = asyncio.create_task(self._read_stream("stdout"))
        stderr_task = asyncio.create_task(self._read_stream("stderr"))
        try:
            result = await asyncio.wait_for(self._process.wait(), self.node.timeout)
            return NodeResult.FAIL if result else NodeResult.SUCCESS
        except asyncio.TimeoutError:
            logger.debug(f"Node {self.node.name} timeout")
            return NodeResult.TIMEOUT
        except asyncio.CancelledError:
            logger.debug(f"Node {self.node.name} canceled")
            return NodeResult.CANCEL
        finally:
            self._terminate()
            await asyncio.gather(stdout_task, stderr_task)
            await self._process.wait()

    async def _execute_children(self) -> NodeResult:
        if not self.node.children:
            return NodeResult.SUCCESS

        children = self.node.children
        executors = [NodeExecutor(self.workflow, child, self.servicer) for child in children]
        tasks = [asyncio.create_task(executor.execute()) for executor in executors]
        for result in asyncio.as_completed(tasks):
            if await result:
                _cancel_tasks(tasks)
                return NodeResult.CHILD_FAILED
        return NodeResult.SUCCESS


def _cancel_tasks(tasks: list[asyncio.Task[NodeResult]]) -> None:
    for task in tasks:
        task.cancel()
