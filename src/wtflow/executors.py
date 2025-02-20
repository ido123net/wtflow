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
from wtflow.executables import Command, Executable, PyFunc

if typing.TYPE_CHECKING:  # pragma: no cover
    from wtflow.nodes import Node

multiprocessing.set_start_method("spawn", force=True)

logger = logging.getLogger(__name__)


class CommandFailed(Exception):
    """Command failed."""


async def async_execute(executalbe: Executable, timeout: int | None = None) -> Result:
    if isinstance(executalbe, Command):
        return await _async_subprocess_execute(executalbe, timeout)
    elif isinstance(executalbe, PyFunc):
        return await _async_py_func_execute(executalbe, timeout)
    else:  # pragma: no cover
        raise TypeError(f"Invalid executalbe type: {type(executalbe)}")


async def _async_subprocess_execute(command: Command, timeout: int | None = None) -> Result:
    process = await asyncio.create_subprocess_shell(
        command.cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    try:
        async with asyncio.timeout(timeout):
            retcode = await process.wait()
            assert process.stdout
            assert process.stderr
            stdout, stderr = await asyncio.gather(process.stdout.read(), process.stderr.read())
    except asyncio.TimeoutError:
        process.terminate()
        await process.wait()
        raise

    return Result(retcode=retcode, stdout=stdout, stderr=stderr)


async def _async_py_func_execute(pyfunc: PyFunc, timeout: int | None = None) -> Result:
    stdout = FileLikeQueue()
    stderr = FileLikeQueue()

    process = multiprocessing.Process(
        target=_std_redirect,
        args=(pyfunc.func, stdout, stderr, *pyfunc.args),
        kwargs=pyfunc.kwargs,
    )
    process.start()

    try:
        async with asyncio.timeout(timeout):
            while process.is_alive():
                await asyncio.sleep(0.1)
    except asyncio.TimeoutError:
        process.terminate()
        process.join(5)
        if process.is_alive():  # pragma: no cover
            process.kill()
        raise

    retcode = process.exitcode
    stdout_data, stderr_data = await asyncio.gather(asyncio.to_thread(stdout.read), asyncio.to_thread(stderr.read))

    return Result(retcode=retcode, stdout=stdout_data.encode(), stderr=stderr_data.encode())


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


class NodeExecutor:
    def __init__(self, node: Node):
        self.node = node

    async def execute(self) -> None:
        try:
            if self.node.executable:
                logger.debug(f"Executing function: {self.node.executable}")
                self.node.result = await async_execute(self.node.executable, self.node.timeout)
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
