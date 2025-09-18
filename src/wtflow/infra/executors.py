from __future__ import annotations

import logging
import multiprocessing
import os
import signal
import subprocess
import sys
import traceback
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor
from typing import IO, TYPE_CHECKING, Callable, NamedTuple

if TYPE_CHECKING:
    from wtflow.infra.executables import Command, Executable, PyFunc


logger = logging.getLogger(__name__)


class Result(NamedTuple):
    retcode: int | None
    stdout: bytes
    stderr: bytes


def _read_stream(stream: IO[bytes], callback: Callable[[bytes], int]) -> bytes:
    res = b""
    for line in iter(stream.readline, b""):
        callback(line)
        res += line
    return res


class Executor(ABC):
    """Base class for execution logic."""

    def __init__(self, executable: Executable) -> None:
        self._executable = executable
        self._stdout_stream: IO[bytes] | None = None
        self._stderr_stream: IO[bytes] | None = None

    @abstractmethod
    def execute(self, executable: Executable) -> None: ...

    @abstractmethod
    def wait(self, executable: Executable) -> int | None: ...

    def _wait(self, executable: Executable) -> Result:
        assert self._stdout_stream is not None and self._stderr_stream is not None
        with ThreadPoolExecutor(max_workers=3) as pool:
            retcode_f = pool.submit(self.wait, executable)
            stdout_f = pool.submit(_read_stream, self._stdout_stream, lambda line: sys.stdout.buffer.write(line))
            stderr_f = pool.submit(_read_stream, self._stderr_stream, lambda line: sys.stderr.buffer.write(line))

        return Result(retcode_f.result(), stdout_f.result(), stderr_f.result())


class MultiprocessingExecutor(Executor):
    """Runs a Python function asynchronously in a separate process using os.pipe."""

    def execute(self, executable: Executable) -> None:
        if TYPE_CHECKING:
            assert isinstance(executable, PyFunc)
        stdout_rx, stdout_tx = os.pipe()
        stderr_rx, stderr_tx = os.pipe()

        def _target() -> None:
            sys.stdout = os.fdopen(stdout_tx, "w", buffering=1)
            sys.stderr = os.fdopen(stderr_tx, "w", buffering=1)
            try:
                executable.func(*executable.args, **executable.kwargs)
            except Exception:
                traceback.print_exc()
                raise
            finally:
                sys.stdout.close()
                sys.stderr.close()

        self._process = multiprocessing.Process(target=_target)
        self._process.start()
        self._stdout_stream = os.fdopen(stdout_rx, "rb")
        self._stderr_stream = os.fdopen(stderr_rx, "rb")
        os.close(stdout_tx)
        os.close(stderr_tx)

    def wait(self, executable: Executable) -> int | None:
        if TYPE_CHECKING:
            assert isinstance(executable, PyFunc)
        self._process.join(executable.timeout)
        if self._process.is_alive():
            self._process.terminate()
            self._process.join()
        return self._process.exitcode


class SubprocessExecutor(Executor):
    """Runs an external command asynchronously using subprocess."""

    def execute(self, executable: Executable) -> None:
        if TYPE_CHECKING:
            assert isinstance(executable, Command)
        self._process = subprocess.Popen(
            executable.cmd,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            start_new_session=True,
        )
        self._stdout_stream = self._process.stdout
        self._stderr_stream = self._process.stderr

    def wait(self, executable: Executable) -> int | None:
        if TYPE_CHECKING:
            assert isinstance(executable, Command)
        try:
            return self._process.wait(executable.timeout)
        except (subprocess.TimeoutExpired, KeyboardInterrupt):
            os.killpg(os.getpgid(self._process.pid), signal.SIGTERM)
            return self._process.wait()
