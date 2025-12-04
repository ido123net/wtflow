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
from typing import IO, Callable, NamedTuple

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
    stream.close()
    return res


class Executor(ABC):
    """Base class for execution logic."""

    def __init__(self, executable: Executable) -> None:
        self.executable = executable
        self.stdout: IO[bytes] | None = None
        self.stderr: IO[bytes] | None = None

    @abstractmethod
    def _execute(self, executable: Executable) -> None: ...

    @abstractmethod
    def _wait(self, executable: Executable) -> int | None: ...

    def execute(self) -> Result:
        self._execute(self.executable)
        return self.wait()

    def wait(self) -> Result:
        assert self.stdout is not None and self.stderr is not None
        _stdout = sys.stdout.buffer
        _stderr = sys.stderr.buffer
        with ThreadPoolExecutor(max_workers=3) as pool:
            retcode_f = pool.submit(self._wait, self.executable)
            stdout_f = pool.submit(_read_stream, self.stdout, lambda line: _stdout.write(line))
            stderr_f = pool.submit(_read_stream, self.stderr, lambda line: _stderr.write(line))

        return Result(retcode_f.result(), stdout_f.result(), stderr_f.result())


class MultiprocessingExecutor(Executor):
    """Runs a Python function asynchronously in a separate process using os.pipe."""

    def _execute(self, executable: Executable) -> None:
        if not isinstance(executable, PyFunc):
            raise TypeError(f"expected PyFunc, not {type(executable).__name__}")
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

        self._process = multiprocessing.get_context("fork").Process(target=_target)
        self._process.start()
        self.stdout = os.fdopen(stdout_rx, "rb")
        self.stderr = os.fdopen(stderr_rx, "rb")
        os.close(stdout_tx)
        os.close(stderr_tx)

    def _wait(self, executable: Executable) -> int | None:
        if not isinstance(executable, PyFunc):
            raise TypeError(f"expected PyFunc, not {type(executable).__name__}")
        self._process.join(executable.timeout)
        if self._process.is_alive():
            self._process.terminate()
            self._process.join()
        return self._process.exitcode


class SubprocessExecutor(Executor):
    """Runs an external command asynchronously using subprocess."""

    def _execute(self, executable: Executable) -> None:
        if not isinstance(executable, Command):
            raise TypeError(f"expected Command, not {type(executable).__name__}")
        self._process = subprocess.Popen(
            executable.cmd,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            start_new_session=True,
        )
        self.stdout = self._process.stdout
        self.stderr = self._process.stderr

    def _wait(self, executable: Executable) -> int | None:
        if not isinstance(executable, Command):
            raise TypeError(f"expected Command, not {type(executable).__name__}")
        try:
            return self._process.wait(executable.timeout)
        except (subprocess.TimeoutExpired, KeyboardInterrupt):
            os.killpg(os.getpgid(self._process.pid), signal.SIGTERM)
            return self._process.wait()


def get_executor(executable: Executable) -> Executor:
    executor = executable.get_executor()
    return executor(executable)
