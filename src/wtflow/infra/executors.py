from __future__ import annotations

import os
import signal
import subprocess


class Executor:
    def __init__(
        self,
        command: str,
        timeout: float | None,
        stdout: int | None = None,
        stderr: int | None = None,
    ) -> None:
        self.command = command
        self.timeout = timeout
        self.stdout = stdout
        self.stderr = stderr

    def execute(self) -> int | None:
        self._execute()
        return self._wait()

    def _execute(self) -> None:
        self.process = subprocess.Popen(
            self.command,
            shell=True,
            stdout=self.stdout,
            stderr=self.stderr,
            start_new_session=True,
        )

    def _wait(self) -> int | None:
        try:
            return self.process.wait(self.timeout)
        except (subprocess.TimeoutExpired, KeyboardInterrupt):
            os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)
            return self.process.wait()
