from __future__ import annotations

import io
import logging
import multiprocessing
import os
import pathlib
import signal
import subprocess
import sys
import traceback
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor
from multiprocessing.connection import Connection
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
    def _wait(self, executable: Executable) -> int | None: ...

    def wait(
        self,
        executable: Executable,
        stdout: pathlib.Path | None = None,
        stderr: pathlib.Path | None = None,
    ) -> Result:
        assert self._stdout_stream is not None and self._stderr_stream is not None
        if stdout is not None:
            stdout.parent.mkdir(parents=True, exist_ok=True)
        if stderr is not None:
            stderr.parent.mkdir(parents=True, exist_ok=True)
        _stdout = open(stdout, "wb") if stdout else sys.stdout.buffer
        _stderr = open(stderr, "wb") if stderr else sys.stderr.buffer
        with ThreadPoolExecutor(max_workers=3) as pool:
            retcode_f = pool.submit(self._wait, executable)
            stdout_f = pool.submit(_read_stream, self._stdout_stream, lambda line: _stdout.write(line))
            stderr_f = pool.submit(_read_stream, self._stderr_stream, lambda line: _stderr.write(line))

        return Result(retcode_f.result(), stdout_f.result(), stderr_f.result())


class ConnReader(io.RawIOBase, IO[bytes]):
    def __init__(self, conn: Connection[bytes, bytes]):
        self._conn = conn
        self._buf = bytearray()
        super().__init__()

    def read(self, size: int = -1) -> bytes:
        while size < 0 or len(self._buf) < size:
            try:
                chunk = self._conn.recv_bytes()
            except EOFError:
                break
            self._buf.extend(chunk)
        res = self._buf[:size]
        self._buf = self._buf[size:]
        return bytes(res)


class ConnWriter(io.TextIOBase, IO[str]):
    def __init__(self, conn: Connection[bytes, bytes]):
        self._conn = conn
        super().__init__()

    def write(self, s: str) -> int:
        data = s.encode("utf-8")
        self._conn.send_bytes(data)
        return len(data)


def _wrapped_target(stdout_tx: ConnWriter, stderr_tx: ConnWriter, executable: PyFunc) -> None:
    sys.stdout = stdout_tx
    sys.stderr = stderr_tx
    try:
        executable.func(*executable.args, **executable.kwargs)
    except Exception:
        traceback.print_exc()
        raise
    finally:
        sys.stdout.close()
        sys.stderr.close()


class MultiprocessingExecutor(Executor):
    """Runs a Python function asynchronously in a separate process using os.pipe."""

    def execute(self, executable: Executable) -> None:
        if TYPE_CHECKING:
            assert isinstance(executable, PyFunc)
        stdout_rx, stdout_tx = multiprocessing.Pipe(duplex=False)
        stderr_rx, stderr_tx = multiprocessing.Pipe(duplex=False)

        self._process = multiprocessing.get_context("spawn").Process(
            target=_wrapped_target,
            args=(ConnWriter(stdout_tx), ConnWriter(stderr_tx), executable),
            daemon=True,
        )
        self._process.start()
        self._stdout_stream = ConnReader(stdout_rx)
        self._stderr_stream = ConnReader(stderr_rx)

    def _wait(self, executable: Executable) -> int | None:
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

    def _wait(self, executable: Executable) -> int | None:
        if TYPE_CHECKING:
            assert isinstance(executable, Command)
        try:
            return self._process.wait(executable.timeout)
        except (subprocess.TimeoutExpired, KeyboardInterrupt):
            os.killpg(os.getpgid(self._process.pid), signal.SIGTERM)
            return self._process.wait()
