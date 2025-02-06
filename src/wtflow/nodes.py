from __future__ import annotations

import asyncio
import logging
from enum import StrEnum, auto
from uuid import uuid4

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class CommandFailed(Exception):
    """Command failed."""


class Outcome(StrEnum):
    INITIAL = auto()
    SUCCESS = auto()
    FAILURE = auto()
    TIMEOUT = auto()
    STOPPED = auto()


class Result(BaseModel):
    retcode: int | None = None
    stdout: bytes = Field(b"", exclude=True)
    stderr: bytes = Field(b"", exclude=True)


class Node(BaseModel):
    node_id: str = Field(default_factory=lambda: str(uuid4().hex), exclude=True)
    name: str
    outcome: Outcome = Outcome.INITIAL
    cmd: str | None = None
    stop_on_failure: bool = False
    timeout: int | None = None
    result: Result | None = None
    parallel: bool = False
    children: list[Node] = []
    _parent: Node | None = None

    def model_post_init(self, __context):
        if self.children:
            for child in self.children:
                child._parent = self
        return super().model_post_init(__context)

    @property
    def parent(self) -> Node | None:
        return self._parent  # pragma: no cover

    async def execute(self):
        await NodeExecutor(self).execute()


class NodeExecutor:
    def __init__(self, node: Node):
        self.node = node

    async def execute(self):
        process = None
        retcode = None
        stdout = stderr = b""
        try:
            if self.node.cmd:
                logger.debug(f"Executing command: {self.node.cmd}")
                process_task = asyncio.create_subprocess_shell(
                    self.node.cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                async with asyncio.timeout(self.node.timeout):
                    process = await process_task
                    async for line in process.stdout:
                        stdout += line
                    async for line in process.stderr:
                        stderr += line
                    retcode = await process.wait()
                    if self.node.stop_on_failure and retcode:
                        raise CommandFailed
            await self.execute_children()
        except asyncio.CancelledError:
            self.node.outcome = Outcome.STOPPED
            raise
        except asyncio.TimeoutError:
            self.node.outcome = Outcome.TIMEOUT
            if self.node.stop_on_failure:
                raise asyncio.CancelledError("Timeout")
        except CommandFailed:
            self.node.outcome = Outcome.FAILURE
            raise asyncio.CancelledError("Error")
        else:
            self.node.outcome = Outcome.SUCCESS
        finally:
            if process and process.returncode is None:
                await self.terminate_process(process)
            if retcode is not None:
                self.node.result = Result(retcode=retcode, stdout=stdout, stderr=stderr)

    async def terminate_process(self, process: asyncio.subprocess.Process):
        process.terminate()
        try:
            async with asyncio.timeout(5):
                await process.wait()
        except asyncio.TimeoutError:  # pragma: no cover
            process.kill()
        await process.wait()

    async def execute_children(self):
        if self.node.parallel:
            await asyncio.gather(*(child.execute() for child in self.node.children))
        else:
            for child in self.node.children:
                await child.execute()
