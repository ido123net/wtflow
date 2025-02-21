from __future__ import annotations

import asyncio
import contextlib
import logging
import multiprocessing
import os
import traceback
import typing

from wtflow.definitions import Outcome, Result
from wtflow.executables import Command, Executable, PyFunc

if typing.TYPE_CHECKING:  # pragma: no cover
    from wtflow.nodes import Node


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


def _target_wrapper(
    func: typing.Callable[..., typing.Any] | str,
    write_fd_out: int,
    write_fd_err: int,
) -> typing.Callable[..., typing.Any]:
    assert not isinstance(func, str)

    def inner(*args: typing.Any, **kwargs: typing.Any) -> typing.Any:
        stdout = os.fdopen(write_fd_out, "w", buffering=1)
        stderr = os.fdopen(write_fd_err, "w", buffering=1)
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            try:
                return func(*args, **kwargs)
            except Exception:
                traceback.print_exc()
                raise
            finally:
                stdout.close()
                stderr.close()

    return inner


async def _async_py_func_execute(
    pyfunc: PyFunc,
    timeout: int | None = None,
) -> Result:
    read_fd_out, write_fd_out = os.pipe()
    read_fd_err, write_fd_err = os.pipe()

    process = multiprocessing.Process(
        target=_target_wrapper(pyfunc.func, write_fd_out, write_fd_err),
        args=pyfunc.args,
        kwargs=pyfunc.kwargs,
    )
    process.start()
    os.close(write_fd_out)
    os.close(write_fd_err)

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

    with os.fdopen(read_fd_out, "r") as stdout, os.fdopen(read_fd_err, "r") as stderr:
        return Result(
            retcode=retcode,
            stdout=stdout.read().encode(),
            stderr=stderr.read().encode(),
        )


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
