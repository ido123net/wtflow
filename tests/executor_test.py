from __future__ import annotations

from wtflow.infra.executors import Executor


def test_timeout(capfdbinary):
    executor = Executor(command="sleep 5 && echo hello", timeout=0.1)
    result = executor.execute()
    assert result == -15
    stdout, stderr = capfdbinary.readouterr()
    assert stdout == b""
    assert stderr == b""


def test_partial_stdout(capfdbinary):
    executor = Executor(command="echo 'Hello' && sleep 2 && echo 'World'", timeout=0.1)
    result = executor.execute()
    assert result == -15
    stdout, stderr = capfdbinary.readouterr()
    assert stdout == b"Hello\n"
    assert stderr == b""
