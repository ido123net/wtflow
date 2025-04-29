import os
import time

import pytest

from wtflow.engine import Engine
from wtflow.executables import Command, PyFunc
from wtflow.nodes import Node
from wtflow.workflow import Workflow


@pytest.fixture(autouse=True, scope="session")
def set_env(tmp_path_factory):
    data_dir = tmp_path_factory.mktemp("data")
    os.environ["WTFLOW_ARTIFACTS_DIR"] = str(data_dir)
    os.environ["WTFLOW_DB_URL"] = f"sqlite:///{data_dir}/test.db"


def test_run():
    wf = Workflow(
        name="test run",
        root=Node(
            name="Root Node",
            children=[
                Node(name="Node 1", executable=Command(cmd='echo "Hello 1"')),
                Node(
                    name="Node 2",
                    parallel=True,
                    children=[
                        Node(name="Node 2.1", executable=Command(cmd='echo "World 2.1"')),
                        Node(name="Node 2.2", executable=Command(cmd='echo "World 2.2"')),
                    ],
                ),
            ],
        ),
    )
    engine = Engine(wf)
    engine.run()


def test_fail_run():
    wf = Workflow(
        name="test fail run",
        root=Node(
            name="fail node",
            executable=Command(cmd="command-not-exist"),
        ),
    )
    engine = Engine(wf)
    assert engine.run() == 1
    assert b"not found" in engine.workflow.root.stderr


def test_stop_on_failure():
    wf = Workflow(
        name="test stop on failure",
        root=Node(
            name="Root Node",
            children=[
                Node(name="Node 1", executable=Command(cmd='echo "Hello 1"')),
                Node(
                    name="Node 2",
                    parallel=True,
                    children=[
                        Node(name="Node 2.1", executable=Command(cmd='echo "World 2.1"')),
                        Node(name="Node 2.2", executable=Command(cmd="command-not-exist")),
                    ],
                ),
                Node(name="Node 3", executable=Command(cmd='echo "Hello 3"')),
            ],
        ),
    )
    engine = Engine(wf)
    assert engine.run() == 1
    assert engine.workflow.root.children[2].retcode is None


def test_timeout():
    wf = Workflow(
        name="test timeout",
        root=Node(
            name="Root Node",
            executable=Command(cmd="sleep 5", timeout=0.1),
        ),
    )
    engine = Engine(wf)
    assert engine.run() == 1


def func(*args, **kwargs):
    print(args, kwargs)


def test_PyFunc_executable():
    wf = Workflow(
        name="test PyFunc executable",
        root=Node(
            name="Root Node",
            executable=PyFunc(func, args=(1, 2), kwargs={"a": 1}),
        ),
    )
    engine = Engine(wf)
    assert engine.run() == 0
    assert engine.workflow.root.stdout == b"(1, 2) {'a': 1}\n"
    assert engine.workflow.root.stderr == b""


def _f_sleep():
    time.sleep(2)  # pragma: no cover (for testing timeout)


def test_PyFunc_timeout():
    wf = Workflow(
        name="test PyFunc timeout",
        root=Node(
            name="Root Node",
            executable=PyFunc(_f_sleep, timeout=0.1),
        ),
    )
    engine = Engine(wf)
    assert engine.run() == 1


def _f_exception():
    raise Exception("Test exception")


def test_PyFunc_exception():
    wf = Workflow(
        name="test PyFunc exception",
        root=Node(
            name="Root Node",
            executable=PyFunc(func=_f_exception),
        ),
    )
    engine = Engine(wf)
    assert engine.run() == 1


def test_partial_stdout():
    wf = Workflow(
        name="test partial stdout",
        root=Node(
            name="Root Node",
            executable=Command(cmd="echo 'Hello' && sleep 2 && echo 'World'", timeout=0.1),
        ),
    )
    engine = Engine(wf)
    engine.run()
    assert engine.workflow.root.stdout == b"Hello\n"


def _f_partial_stdout():  # pragma: no cover (this will only run partially)
    print("Hello")
    time.sleep(2)
    print("World")


def test_partial_stdout_pyfunc():
    wf = Workflow(
        name="test partial stdout pyfunc",
        root=Node(
            name="Root Node",
            executable=PyFunc(_f_partial_stdout, timeout=0.1),
        ),
    )
    engine = Engine(wf)
    engine.run()
    assert engine.workflow.root.stdout == b"Hello\n"


def test_continue_on_failure():
    wf = Workflow(
        name="test continue on failure",
        root=Node(
            name="Root Node",
            children=[
                Node(name="Node 1", executable=Command(cmd="command-not-exist")),
                Node(name="Node 2", executable=Command(cmd="echo run anyway")),
            ],
        ),
    )
    engine = Engine(wf, stop_on_failure=False)
    assert engine.run() == 1
    assert engine.workflow.root.children[1].stdout == b"run anyway\n"


def test_without_config(monkeypatch, capsys):
    monkeypatch.delenv("WTFLOW_ARTIFACTS_DIR")
    wf = Workflow(
        name="test without config",
        root=Node(
            name="Root Node",
            executable=Command(cmd="echo 'Hello world'"),
        ),
    )
    engine = Engine(wf)
    assert engine.run() == 0
    assert capsys.readouterr().out == "Hello world\n"
