from __future__ import annotations

import os
import signal
import subprocess
from typing import IO, NamedTuple


class Result(NamedTuple):
    retcode: int | None
    stdout: bytes
    stderr: bytes


class Executor:
    def __init__(self, command: str, timeout: float | None) -> None:
        self.command = command
        self.timeout = timeout
        self.stdout: IO[bytes] | None = None
        self.stderr: IO[bytes] | None = None

    def execute(self) -> Result:
        self._execute(self.command)
        retcode = self._wait(self.timeout)
        return Result(retcode, b"", b"")

    def _execute(self, command: str, stdout: int | None = None, stderr: int | None = None) -> None:
        self._process = subprocess.Popen(
            command,
            shell=True,
            stdout=stdout,
            stderr=stderr,
            start_new_session=True,
        )

    def _wait(self, timeout: float | None) -> int | None:
        try:
            return self._process.wait(timeout)
        except (subprocess.TimeoutExpired, KeyboardInterrupt):
            os.killpg(os.getpgid(self._process.pid), signal.SIGTERM)
            return self._process.wait()
