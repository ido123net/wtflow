import time

import pytest

from wtflow.artifact import Artifact
from wtflow.config import Config, DatabaseConfig, RunConfig, StorageConfig
from wtflow.engine import Engine
from wtflow.executables import Command, PyFunc
from wtflow.nodes import Node
from wtflow.workflow import Workflow


@pytest.fixture()
def data_dir(tmp_path_factory):
    data_dir = tmp_path_factory.mktemp("data")
    return data_dir


@pytest.fixture()
def storage_config(data_dir):
    artifacts_dir = data_dir / "artifacts"
    return StorageConfig(artifacts_dir=artifacts_dir)


@pytest.fixture()
def db_config(data_dir):
    url = f"sqlite:///{data_dir}/test.db"
    return DatabaseConfig(url=url)


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
    config = Config(run=RunConfig(ignore_failure=True))
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
    engine = Engine(wf, config=config)
    assert engine.run() == 1
    assert engine.workflow.root.children[1].stdout == b"run anyway\n"


def test_max_fail():
    config = Config(run=RunConfig(max_fail=1))
    wf = Workflow(
        name="test max fail",
        root=Node(
            name="Root Node",
            children=[
                Node(name="Node 1", executable=Command(cmd="command-not-exist")),
                Node(name="Node 2", executable=Command(cmd="command-not-exist")),
                Node(name="Node 3", executable=Command(cmd="echo run anyway")),
            ],
        ),
    )
    engine = Engine(wf, config=config)
    assert engine.run() == 1
    assert engine.workflow.root.children[2].stdout is None


def test_artifact_config(storage_config, capsys):
    config = Config(storage=storage_config)
    node = Node(
        name="Root Node",
        executable=Command(cmd="echo 'Hello world'"),
        children=[Node(name="Node 1", executable=Command(cmd="echo 'Hello'"))],
    )
    wf = Workflow(
        name="test without config",
        root=node,
    )
    engine = Engine(wf, config=config)
    assert engine.run() == 0
    assert capsys.readouterr().out == ""
    with open(storage_config.artifacts_dir / wf.id / node.id / "stdout.txt", "rb") as f:
        assert f.read() == b"Hello world\n"


def test_artifact_and_db_config(storage_config, db_config):
    config = Config(storage=storage_config, db=db_config)
    node = Node(
        name="Root Node",
        executable=Command(cmd="echo 'Hello world'"),
        children=[Node(name="Node 1", executable=Command(cmd="echo 'Hello'"))],
    )
    wf = Workflow(
        name="test with db",
        root=node,
    )
    engine = Engine(wf, config=config)
    assert engine.run() == 0
    with open(storage_config.artifacts_dir / wf.id / node.id / "stdout.txt", "rb") as f:
        assert f.read() == b"Hello world\n"


def _passing_artifact_func(artifact: Artifact):
    print(f"data from child1: {artifact.data.decode().strip()}")


def test_passing_artifact():
    n1 = Node(name="Node 1", executable=Command(cmd="echo 'Hello'"))
    wf = Workflow(
        name="test passing artifact",
        root=Node(
            name="Root Node",
            children=[
                n1,
                Node(name="Node 2", executable=PyFunc(func=_passing_artifact_func, args=(n1.stdout_artifact,))),
            ],
        ),
    )
    engine = Engine(wf)
    assert engine.run() == 0
    assert engine.workflow.root.children[1].stdout == b"data from child1: Hello\n"


def test_with_db(db_config):
    config = Config(db=db_config)
    wf = Workflow(
        name="test no db",
        root=Node(
            name="Root Node",
            executable=Command(cmd="echo 'Hello world'"),
            children=[
                Node(name="Node 1", executable=Command(cmd="echo 'Hello'")),
            ],
        ),
    )
    engine = Engine(wf, config=config)
    assert engine.run() == 0
