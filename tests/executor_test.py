from __future__ import annotations

import pytest

from wtflow.infra.executors import Executor


@pytest.mark.asyncio
async def test_timeout(capfdbinary):
    executor = Executor(command="sleep 5 && echo hello", timeout=0.1)
    result = await executor.execute()
    assert result == -15
    stdout, stderr = capfdbinary.readouterr()
    assert stdout == b""
    assert stderr == b""


@pytest.mark.asyncio
async def test_partial_stdout(capfdbinary):
    executor = Executor(command="echo 'Hello' && sleep 2 && echo 'World'", timeout=0.1)
    result = await executor.execute()
    assert result == -15
    stdout, stderr = capfdbinary.readouterr()
    assert stdout == b"Hello\n"
    assert stderr == b""
