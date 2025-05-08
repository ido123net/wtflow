import pytest

from wtflow.config import Config, DatabaseConfig, RunConfig, StorageConfig
from wtflow.infra.artifact import Artifact
from wtflow.infra.engine import Engine
from wtflow.infra.executables import Command, PyFunc
from wtflow.infra.nodes import Node
from wtflow.infra.workflow import Workflow


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


def test_max_fail_config():
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
    with open(storage_config.artifacts_dir / wf.id / node.id / "stdout", "rb") as f:
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
    with open(storage_config.artifacts_dir / wf.id / node.id / "stdout", "rb") as f:
        assert f.read() == b"Hello world\n"


def test_with_db_config(db_config):
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


def func(): ...


def test_dry_run(capsys):
    wf = Workflow(
        name="test dry run",
        root=Node(
            name="Root Node",
            children=[
                Node(name="Node 1", executable=Command(cmd="echo 'Hello'")),
                Node(name="Node 2", executable=PyFunc(func=func)),
            ],
        ),
    )
    engine = Engine(wf, dry_run=True)
    assert engine.run() == 0
    out, _ = capsys.readouterr()
    expected_out = """\
Workflow: test dry run
- Root Node
  - Node 1
    Executable: Command(cmd="echo 'Hello'")
  - Node 2
    Executable: PyFunc(<tests.engine_test.func>)
"""
    assert out == expected_out
