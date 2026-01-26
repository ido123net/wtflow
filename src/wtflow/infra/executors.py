from __future__ import annotations

import os
import signal
import subprocess
from typing import NamedTuple


class Result(NamedTuple):
    retcode: int | None
    stdout: bytes
    stderr: bytes


class Executor:
    def __init__(self, command: str, timeout: float | None) -> None:
        self.command = command
        self.timeout = timeout

    def execute(self) -> Result:
        self._execute(pipe=False)
        retcode = self._wait()
        return Result(retcode, b"", b"")

    def _execute(self, *, pipe: bool = True) -> None:
        pipe_output = subprocess.PIPE if pipe else None
        self.process = subprocess.Popen(
            self.command,
            shell=True,
            stdout=pipe_output,
            stderr=pipe_output,
            start_new_session=True,
        )

    def _wait(self) -> int | None:
        try:
            return self.process.wait(self.timeout)
        except (subprocess.TimeoutExpired, KeyboardInterrupt):
            os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)
            return self.process.wait()
