from __future__ import annotations

import os
import signal
import subprocess
from typing import IO, NamedTuple

from wtflow.infra.executables import Command


class Result(NamedTuple):
    retcode: int | None
    stdout: bytes
    stderr: bytes


class Executor:
    def __init__(self, executable: Command) -> None:
        self.executable = executable
        self.stdout: IO[bytes] | None = None
        self.stderr: IO[bytes] | None = None

    def execute(self) -> Result:
        self._execute(self.executable)
        retcode = self._wait(self.executable)
        return Result(retcode, b"", b"")

    def _execute(self, executable: Command, stdout: int | None = None, stderr: int | None = None) -> None:
        self._process = subprocess.Popen(
            executable.cmd,
            shell=True,
            stdout=stdout,
            stderr=stderr,
            start_new_session=True,
        )

    def _wait(self, executable: Command) -> int | None:
        try:
            return self._process.wait(executable.timeout)
        except (subprocess.TimeoutExpired, KeyboardInterrupt):
            os.killpg(os.getpgid(self._process.pid), signal.SIGTERM)
            return self._process.wait()
