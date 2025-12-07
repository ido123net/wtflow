from __future__ import annotations

import time

from wtflow.infra.executables import Command, PyFunc
from wtflow.infra.executors import get_executor


def test_timeout(capfdbinary):
    executable = Command(cmd="sleep 5 && echo hello", timeout=0.1)
    executor = get_executor(executable)
    result = executor.execute()
    assert result.retcode == -15
    assert result.stdout == b""
    assert result.stderr == b""
    stdout, stderr = capfdbinary.readouterr()
    assert stdout == b""
    assert stderr == b""


def func(*args, **kwargs):
    print(args, kwargs)


def test_PyFunc_executable(capfdbinary):
    executable = PyFunc(func, args=(1, 2), kwargs={"a": 1})
    executor = get_executor(executable)
    result = executor.execute()
    assert result.retcode == 0
    stdout, stderr = capfdbinary.readouterr()
    assert stdout == b"(1, 2) {'a': 1}\n"
    assert stderr == b""


def _f_sleep():  # pragma: no cover (for testing timeout)
    time.sleep(2)
    print("hello")


def test_PyFunc_timeout(capfdbinary):
    executable = PyFunc(_f_sleep, timeout=0.1)
    executor = get_executor(executable)
    result = executor.execute()
    assert result.retcode == -15
    stdout, stderr = capfdbinary.readouterr()
    assert stdout == b""
    assert stderr == b""


def _f_exception():
    raise Exception("Test exception")


def test_PyFunc_exception(capfdbinary):
    executable = PyFunc(func=_f_exception)
    executor = get_executor(executable)
    result = executor.execute()
    assert result.retcode == 1
    stdout, stderr = capfdbinary.readouterr()
    assert stdout == b""
    assert b"Traceback (most recent call last):\n" in stderr
    assert b"Exception: Test exception" in stderr


def test_partial_stdout(capfdbinary):
    executable = Command(cmd="echo 'Hello' && sleep 2 && echo 'World'", timeout=0.1)
    executor = get_executor(executable)
    result = executor.execute()
    assert result.retcode == -15
    stdout, stderr = capfdbinary.readouterr()
    assert stdout == b"Hello\n"
    assert stderr == b""


def _f_partial_stdout():  # pragma: no cover (this will only run partially)
    print("Hello")
    time.sleep(2)
    print("World")


def test_partial_stdout_pyfunc(capfdbinary):
    executable = PyFunc(_f_partial_stdout, timeout=0.1)
    executor = get_executor(executable)
    result = executor.execute()
    assert result.retcode == -15
    stdout, stderr = capfdbinary.readouterr()
    assert stdout == b"Hello\n"
    assert stderr == b""
