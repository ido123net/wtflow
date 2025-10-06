import pytest

from wtflow.infra.executables import Command, PyFunc
from wtflow.infra.executors import MultiprocessingExecutor, SubprocessExecutor


def test_subprocess_executor_with_py_func():
    py_func = PyFunc(lambda: "")
    executor = SubprocessExecutor(py_func)
    with pytest.raises(TypeError, match="expected Command, not PyFunc"):
        executor._execute(py_func)

    with pytest.raises(TypeError, match="expected Command, not PyFunc"):
        executor._wait(py_func)


def test_multiprocessing_executor_with_command():
    command = Command("")
    executor = MultiprocessingExecutor(command)
    with pytest.raises(TypeError, match="expected PyFunc, not Command"):
        executor._execute(command)

    with pytest.raises(TypeError, match="expected PyFunc, not Command"):
        executor._wait(command)
