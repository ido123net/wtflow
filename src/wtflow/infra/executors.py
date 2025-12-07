from __future__ import annotations

import multiprocessing
import os
import signal
import subprocess
import sys
import traceback
from abc import ABC, abstractmethod
from typing import IO, NamedTuple

from wtflow.infra.executables import Command, Executable, PyFunc


class Result(NamedTuple):
    retcode: int | None
    stdout: bytes
    stderr: bytes


class Executor(ABC):
    """Base class for execution logic."""

    def __init__(self, executable: Executable) -> None:
        self.executable = executable
        self.stdout: IO[bytes] | None = None
        self.stderr: IO[bytes] | None = None

    @abstractmethod
    def _execute(self, executable: Executable, stdout: int | None = None, stderr: int | None = None) -> None: ...

    @abstractmethod
    def _wait(self, executable: Executable) -> int | None: ...

    def execute(self) -> Result:
        self._execute(self.executable)
        retcode = self._wait(self.executable)
        return Result(retcode, b"", b"")


class MultiprocessingExecutor(Executor):
    """Runs a Python function asynchronously in a separate process using os.pipe."""

    def _execute(self, executable: Executable, stdout: int | None = None, stderr: int | None = None) -> None:
        if not isinstance(executable, PyFunc):
            raise TypeError(f"expected PyFunc, not {type(executable).__name__}")

        def _target() -> None:
            if stdout:
                sys.stdout = os.fdopen(stdout, "w", buffering=1)
            if stderr:
                sys.stderr = os.fdopen(stderr, "w", buffering=1)
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

    def _execute(self, executable: Executable, stdout: int | None = None, stderr: int | None = None) -> None:
        if not isinstance(executable, Command):
            raise TypeError(f"expected Command, not {type(executable).__name__}")
        self._process = subprocess.Popen(
            executable.cmd,
            shell=True,
            stdout=stdout,
            stderr=stderr,
            start_new_session=True,
        )

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
