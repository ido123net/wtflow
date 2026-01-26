from __future__ import annotations

import asyncio
import os
import signal


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

    async def execute(self) -> int | None:
        await self._execute()
        return await self._wait()

    async def _execute(self) -> None:
        self.process = await asyncio.create_subprocess_shell(
            self.command,
            shell=True,
            stdout=self.stdout,
            stderr=self.stderr,
            start_new_session=True,
        )

    async def _wait(self) -> int | None:
        try:
            return await asyncio.wait_for(self.process.wait(), self.timeout)
        except asyncio.TimeoutError:
            os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)
            return await self.process.wait()
