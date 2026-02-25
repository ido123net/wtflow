from __future__ import annotations

import asyncio
import logging
import os
import signal
import sys
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
        try:
            self.servicer.start_services()
            return await self._execute()
        finally:
            logger.debug(f"End execution of {self.node.name!r}")
            retcode = await self._process.wait() if self._process else None
            logger.debug(f"Node {self.node.name!r} {retcode = }")
            await self.servicer.db_service.end_execution(self.workflow, self.node, retcode)
            self.servicer.stop_services()

    async def _read_stream(self, name: str) -> None:
        assert self._process is not None
        stream: asyncio.StreamReader = getattr(self._process, name)
        while data := await stream.readline():
            logger.debug(f"got data: {data=}")
            with self.servicer.storage_service.open_artifact(self.workflow, self.node, name) as f:
                if f is not None:
                    os.write(f, data)
                else:
                    getattr(sys, name).write(data.decode())

    def _terminate(self) -> None:
        if self._process and self._process.returncode is None:
            logger.debug("Terminate process")
            os.killpg(os.getpgid(self._process.pid), signal.SIGTERM)

    async def _execute(self) -> NodeResult:
        return await self._execute_command(self.node.command) or await self.execute_children()

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

    async def execute_children(self) -> NodeResult:
        if not self.node.children:
            return NodeResult.SUCCESS

        children = self.node.children
        parallel = self.node.parallel
        executors = [NodeExecutor(self.workflow, child, self.servicer) for child in children]
        if parallel:
            logger.debug(f"Executing {', '.join(repr(child.name) for child in children)} children in parallel")
            tasks = [asyncio.create_task(executor._execute()) for executor in executors]
            for result in asyncio.as_completed(tasks):
                if await result:
                    _cancel_tasks(tasks)
                    return NodeResult.CHILD_FAILED
        else:
            for executor in executors:
                if await executor._execute():
                    return NodeResult.CHILD_FAILED
        return NodeResult.SUCCESS


def _cancel_tasks(tasks: list[asyncio.Task[NodeResult]]) -> None:
    for task in tasks:
        task.cancel()
