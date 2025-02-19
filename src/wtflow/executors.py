from __future__ import annotations

import asyncio
import contextlib
import io
import logging
import multiprocessing
import traceback
import typing
from collections.abc import Buffer

from wtflow.definitions import Outcome, Result
from wtflow.executables import Command, PyFunc

if typing.TYPE_CHECKING:  # pragma: no cover
    from wtflow.nodes import Node

multiprocessing.set_start_method("spawn", force=True)

logger = logging.getLogger(__name__)


class CommandFailed(Exception):
    """Command failed."""


async def command_execute(command: Command, timeout: int | None = None) -> Result:
    process = None
    try:
        async with asyncio.timeout(timeout):
            process = await _run_subprocess(command)
            await process.wait()
    except asyncio.TimeoutError:
        if process:
            process.terminate()
            await process.wait()
        raise

    assert process.stdout
    assert process.stderr
    return Result(retcode=process.returncode, stdout=await process.stdout.read(), stderr=await process.stderr.read())


async def _run_subprocess(command: Command) -> asyncio.subprocess.Process:
    process_task = asyncio.create_subprocess_shell(
        command.cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    return await process_task


class FileLikeQueue(io.StringIO):
    def __init__(self) -> None:
        super().__init__()
        self.queue: multiprocessing.Queue[str] = multiprocessing.Queue()

    def write(self, data: str | Buffer) -> int:
        if isinstance(data, Buffer):  # pragma: no cover
            data = str(data)
        self.queue.put(data)
        return len(data)

    def close(self) -> None:
        self.queue.close()

    def read(self, size: int | None = None) -> str:
        res = ""
        while not self.queue.empty():
            res += self.queue.get()
        return res


def _std_redirect(
    func: typing.Callable[..., typing.Any],
    stdout: FileLikeQueue,
    stderr: FileLikeQueue,
    *args: typing.Any,
    **kwargs: typing.Any,
) -> None:
    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        try:
            func(*args, **kwargs)
        except Exception:
            traceback.print_exc()
            raise


def py_func_execute(
    func: typing.Callable[..., typing.Any] | str,
    timeout: int | None = None,
    *args: typing.Any,
    **kwargs: typing.Any,
) -> Result:
    stdout = FileLikeQueue()
    stderr = FileLikeQueue()

    process = multiprocessing.Process(target=_std_redirect, args=(func, stdout, stderr, *args), kwargs=kwargs)
    process.start()
    process.join(timeout)
    if process.is_alive():
        process.terminate()
        process.join(5)
        if process.is_alive():  # pragma: no cover
            process.kill()
        raise asyncio.TimeoutError
    return Result(retcode=process.exitcode, stdout=stdout.read().encode(), stderr=stderr.read().encode())


class NodeExecutor:
    def __init__(self, node: Node):
        self.node = node

    async def execute(self) -> None:
        try:
            if self.node.cmd:
                logger.debug(f"Executing command: {self.node.cmd}")
                self.node.result = await command_execute(Command(cmd=self.node.cmd), self.node.timeout)
                if self.node.stop_on_failure and self.node.result.retcode:
                    raise CommandFailed
            elif self.node.executable and isinstance(self.node.executable, PyFunc):
                logger.debug(f"Executing function: {self.node.executable}")
                self.node.result = py_func_execute(
                    self.node.executable.func,
                    self.node.timeout,
                    *self.node.executable.args,
                    **self.node.executable.kwargs,
                )
                logger.debug(f"Function returned: {self.node.result}")
                if self.node.stop_on_failure and self.node.result.retcode:
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

    async def execute_children(self) -> None:
        if self.node.parallel:
            await asyncio.gather(*(child.execute() for child in self.node.children))
        else:
            for child in self.node.children:
                await child.execute()
