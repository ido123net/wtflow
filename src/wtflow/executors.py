from __future__ import annotations

import logging
import multiprocessing
import os
import select
import subprocess
import sys
import traceback
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor
from typing import TYPE_CHECKING, NamedTuple

if TYPE_CHECKING:
    from typing import IO

    from wtflow.executables import Command, Executable, PyFunc

logger = logging.getLogger(__name__)


class TimeoutError(Exception):
    pass


class Result(NamedTuple):
    returncode: int | None
    stdout: bytes
    stderr: bytes


class Executor(ABC):
    """Base class for execution logic."""

    def __init__(self, executable: Executable) -> None:
        self._executable = executable
        self.returncode: int | None = None
        self._stdout: bytearray = bytearray()
        self._stderr: bytearray = bytearray()

    @abstractmethod
    def execute(self) -> None:
        """Execute logic, should be overridden by subclasses."""

    @property
    def stdout(self) -> bytes:
        return bytes(self._stdout)

    @property
    def stderr(self) -> bytes:
        return bytes(self._stderr)


class MultiprocessingExecutor(Executor):
    """Runs a Python function asynchronously in a separate process using os.pipe."""

    @property
    def executable(self) -> PyFunc:
        if TYPE_CHECKING:
            assert isinstance(self._executable, PyFunc)
        return self._executable

    def execute(self) -> None:
        stdout_r, stdout_w = os.pipe()
        stderr_r, stderr_w = os.pipe()

        def _target() -> None:
            os.close(stdout_r)
            os.close(stderr_r)

            sys.stdout = os.fdopen(stdout_w, "w", buffering=1)
            sys.stderr = os.fdopen(stderr_w, "w", buffering=1)

            try:
                self.executable.func(*self.executable.args, **self.executable.kwargs)
            except Exception:
                traceback.print_exc()
                raise
            finally:
                sys.stdout.close()
                sys.stderr.close()

        process = multiprocessing.Process(target=_target)
        process.start()
        os.close(stdout_w)
        os.close(stderr_w)

        def _read_pipe(fd: int, storage: bytearray) -> None:
            with os.fdopen(fd, "r", buffering=1) as pipe:
                while chunk := pipe.read(1024):
                    storage.extend(chunk.encode())

        def _wait() -> None:
            process.join(self.executable.timeout)
            if process.is_alive():
                process.terminate()
                process.join()
                self.returncode = process.exitcode
            self.returncode = process.exitcode

        with ThreadPoolExecutor() as pool:
            pool.submit(_read_pipe, stdout_r, self._stdout)
            pool.submit(_read_pipe, stderr_r, self._stderr)
            pool.submit(_wait)


class SubprocessExecutor(Executor):
    """Runs an external command asynchronously using subprocess."""

    @property
    def executable(self) -> Command:
        if TYPE_CHECKING:
            assert isinstance(self._executable, Command)
        return self._executable

    def execute(self) -> None:
        process = subprocess.Popen(
            self.executable.cmd,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        assert process.stdout
        assert process.stderr

        def _read_stream(stream: IO[bytes], storage: bytearray) -> None:
            while True:
                r, _, _ = select.select([stream], [], [], 0.1)
                if not r:
                    break
                chunk = stream.readline()
                if not chunk:
                    break
                storage.extend(chunk)

        def _wait() -> None:
            try:
                self.returncode = process.wait(self.executable.timeout)
            except subprocess.TimeoutExpired:
                process.terminate()
                self.returncode = process.wait()

        with ThreadPoolExecutor() as pool:
            pool.submit(_read_stream, process.stdout, self._stdout)
            pool.submit(_read_stream, process.stderr, self._stderr)
            pool.submit(_wait)
