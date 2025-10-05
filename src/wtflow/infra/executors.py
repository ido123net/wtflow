from __future__ import annotations

import io
import logging
import multiprocessing
import os
import signal
import subprocess
import sys
import traceback
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor
from multiprocessing.connection import Connection
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

    def _execute(self, executable: Executable) -> None:
        if not isinstance(executable, PyFunc):
            raise TypeError(f"expected PyFunc, not {type(executable).__name__}")
        stdout_rx, stdout_tx = multiprocessing.Pipe(duplex=False)
        stderr_rx, stderr_tx = multiprocessing.Pipe(duplex=False)

        self._process = multiprocessing.get_context("spawn").Process(
            target=_wrapped_target,
            args=(ConnWriter(stdout_tx), ConnWriter(stderr_tx), executable),
            daemon=True,
        )
        self._process.start()
        self.stdout = ConnReader(stdout_rx)
        self.stderr = ConnReader(stderr_rx)

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
