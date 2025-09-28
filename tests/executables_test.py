from __future__ import annotations

import time

from wtflow.infra.executables import Command, PyFunc


def test_timeout():
    executable = Command(cmd="sleep 5", timeout=0.1)
    result = executable.execute()
    assert result.retcode == -15
    assert result.stdout == b""
    assert result.stderr == b""


def func(*args, **kwargs):
    print(args, kwargs)


def test_PyFunc_executable():
    executable = PyFunc(func, args=(1, 2), kwargs={"a": 1})
    result = executable.execute()
    assert result.retcode == 0
    assert result.stdout == b"(1, 2) {'a': 1}\n"
    assert result.stderr == b""


def _f_sleep():
    time.sleep(2)  # pragma: no cover (for testing timeout)


def test_PyFunc_timeout():
    executable = PyFunc(_f_sleep, timeout=0.1)
    result = executable.execute()
    assert result.retcode == -15
    assert result.stdout == b""
    assert result.stderr == b""


def _f_exception():
    raise Exception("Test exception")


def test_PyFunc_exception():
    executable = PyFunc(func=_f_exception)
    result = executable.execute()
    assert result.retcode == 1
    assert result.stdout == b""
    assert b"Traceback (most recent call last):\n" in result.stderr
    assert b"Exception: Test exception" in result.stderr


def test_partial_stdout():
    executable = Command(cmd="echo 'Hello' && sleep 2 && echo 'World'", timeout=0.1)
    result = executable.execute()
    assert result.retcode == -15
    assert result.stdout == b"Hello\n"
    assert result.stderr == b""


def _f_partial_stdout():  # pragma: no cover (this will only run partially)
    print("Hello")
    time.sleep(2)
    print("World")


def test_partial_stdout_pyfunc():
    executable = PyFunc(_f_partial_stdout, timeout=1)
    result = executable.execute()
    assert result.retcode == -15
    assert result.stdout == b"Hello\n"
    assert result.stderr == b""
