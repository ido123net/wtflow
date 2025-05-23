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
from functools import partial
from io import FileIO
from typing import IO, TYPE_CHECKING, Callable, NamedTuple

if TYPE_CHECKING:
    from wtflow.infra.artifact import StreamArtifact
    from wtflow.infra.executables import Command, Executable, PyFunc
    from wtflow.infra.nodes import Node


logger = logging.getLogger(__name__)


class Result(NamedTuple):
    retcode: int | None
    stdout: bytes
    stderr: bytes


def _read_stream(stream: IO[bytes], callback: Callable[[bytes], None]) -> bytes:
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
    def _execute(self) -> None:
        """Execute logic, should be overridden by subclasses."""

    def _wait(self) -> int | None:
        """Wait for process completion."""

    @property
    def node(self) -> Node | None:
        return self._executable.node

    def execute(self) -> None:
        self._execute()

    def wait(self) -> Result:
        stdout: FileIO | StreamArtifact
        stderr: FileIO | StreamArtifact
        if self.node:
            stdout, stderr = self.node.stream_artifacts
        else:
            assert isinstance(sys.stdout.buffer, FileIO) and isinstance(sys.stderr.buffer, FileIO)
            stdout, stderr = sys.stdout.buffer, sys.stderr.buffer

        def _callback(stream: FileIO | StreamArtifact, line: bytes) -> None:
            stream.write(line)

        _stdout_callback = partial(_callback, stdout)
        _stderr_callback = partial(_callback, stderr)

        assert self._stdout_stream is not None and self._stderr_stream is not None
        with ThreadPoolExecutor(max_workers=3) as pool:
            retcode_f = pool.submit(self._wait)
            stdout_f = pool.submit(_read_stream, self._stdout_stream, _stdout_callback)
            stderr_f = pool.submit(_read_stream, self._stderr_stream, _stderr_callback)

        return Result(retcode_f.result(), stdout_f.result(), stderr_f.result())


class MultiprocessingExecutor(Executor):
    """Runs a Python function asynchronously in a separate process using os.pipe."""

    @property
    def executable(self) -> PyFunc:
        if TYPE_CHECKING:
            assert isinstance(self._executable, PyFunc)
        return self._executable

    def _execute(self) -> None:
        stdout_rx, stdout_tx = os.pipe()
        stderr_rx, stderr_tx = os.pipe()

        def _target() -> None:
            sys.stdout = os.fdopen(stdout_tx, "w", buffering=1)
            sys.stderr = os.fdopen(stderr_tx, "w", buffering=1)
            try:
                self.executable.func(*self.executable.args, **self.executable.kwargs)
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

    def _wait(self) -> int | None:
        self._process.join(self.executable.timeout)
        if self._process.is_alive():
            self._process.terminate()
            self._process.join()
        return self._process.exitcode


class SubprocessExecutor(Executor):
    """Runs an external command asynchronously using subprocess."""

    @property
    def executable(self) -> Command:
        if TYPE_CHECKING:
            assert isinstance(self._executable, Command)
        return self._executable

    def _execute(self) -> None:
        self._process = subprocess.Popen(
            self.executable.cmd,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            start_new_session=True,
        )
        self._stdout_stream = self._process.stdout
        self._stderr_stream = self._process.stderr

    def _wait(self) -> int | None:
        try:
            return self._process.wait(self.executable.timeout)
        except (subprocess.TimeoutExpired, KeyboardInterrupt):
            os.killpg(os.getpgid(self._process.pid), signal.SIGTERM)
            return self._process.wait()
