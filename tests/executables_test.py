from __future__ import annotations

from wtflow.infra.executables import Command
from wtflow.infra.executors import Executor


def test_timeout(capfdbinary):
    executable = Command(cmd="sleep 5 && echo hello", timeout=0.1)
    executor = Executor(executable)
    result = executor.execute()
    assert result.retcode == -15
    assert result.stdout == b""
    assert result.stderr == b""
    stdout, stderr = capfdbinary.readouterr()
    assert stdout == b""
    assert stderr == b""


def test_partial_stdout(capfdbinary):
    executable = Command(cmd="echo 'Hello' && sleep 2 && echo 'World'", timeout=0.1)
    executor = Executor(executable)
    result = executor.execute()
    assert result.retcode == -15
    stdout, stderr = capfdbinary.readouterr()
    assert stdout == b"Hello\n"
    assert stderr == b""
