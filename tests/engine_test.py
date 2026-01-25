import os

import pytest

from wtflow.config import NO_CONFIG, Config, LocalStorageConfig, RunConfig, Sqlite3Config
from wtflow.infra.engine import Engine
from wtflow.infra.executables import Command
from wtflow.infra.nodes import Node
from wtflow.infra.workflow import Workflow


@pytest.fixture(scope="module", autouse=True)
def no_config():
    os.environ[NO_CONFIG] = "1"
    yield
    del os.environ[NO_CONFIG]


@pytest.fixture()
def data_dir(tmp_path_factory):
    data_dir = tmp_path_factory.mktemp("data")
    return data_dir


@pytest.fixture()
def db_config(data_dir):
    database_path = f"{data_dir}/test.db"
    return Sqlite3Config(database_path=database_path)


@pytest.fixture()
def local_storage_config(data_dir):
    return LocalStorageConfig(base_path=data_dir)


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
    engine = Engine()
    engine.run_workflow(wf)


def test_fail_run():
    wf = Workflow(
        name="test fail run",
        root=Node(
            name="fail node",
            executable=Command(cmd="command-not-exist"),
        ),
    )
    engine = Engine()
    assert engine.run_workflow(wf) == 1
    root_node_result = engine.get_workflow_executor(wf).node_result(wf.root)
    assert root_node_result
    assert b"not found" in root_node_result.stderr


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
    engine = Engine(config=Config())
    assert engine.run_workflow(wf) == 1
    node_result = engine.get_workflow_executor(wf).node_result(wf.root.children[2])
    assert node_result is None


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
    engine = Engine(config=config)
    assert engine.run_workflow(wf) == 1
    node_result = engine.get_workflow_executor(wf).node_result(wf.root.children[1])
    assert node_result
    assert node_result.stdout == b"run anyway\n"


def test_with_db_config(db_config):
    config = Config(database=db_config)
    wf = Workflow(
        name="test with db config",
        root=Node(
            name="Root Node",
            children=[
                Node(name="Node 1", executable=Command(cmd="echo 'Hello'")),
            ],
        ),
    )
    engine = Engine(config=config)
    assert engine.run_workflow(wf) == 0


def test_with_storage_config(local_storage_config, data_dir):
    config = Config(storage=local_storage_config)
    wf = Workflow(
        name="test no db",
        root=Node(
            name="Root Node",
            children=[
                Node(name="Node 1", executable=Command(cmd="echo 'Hello'")),
            ],
        ),
    )
    engine = Engine(config=config)
    assert engine.run_workflow(wf) == 0
    log_path = data_dir / "test no db" / "Node 1" / "stdout.txt"
    assert log_path.exists()
    assert log_path.read_text() == "Hello\n"


def test_with_db_and_storage_config(db_config, local_storage_config):
    config = Config(database=db_config, storage=local_storage_config)
    wf = Workflow(
        name="test with db",
        root=Node(
            name="Root Node",
            children=[
                Node(name="Node 1", executable=Command(cmd="echo 'Hello'")),
            ],
        ),
    )
    engine = Engine(config=config)
    assert engine.run_workflow(wf) == 0


def test_dry_run(capsys):
    wf = Workflow(
        name="test dry run",
        root=Node(
            name="Root Node",
            children=[
                Node(name="Node 1", executable=Command(cmd="echo 'Hello'")),
            ],
        ),
    )
    engine = Engine()
    assert engine.run_workflow(wf, dry_run=True) == 0
    out, _ = capsys.readouterr()
    expected_out = """\
{
  "name": "test dry run",
  "root": {
    "name": "Root Node",
    "children": [
      {
        "name": "Node 1",
        "executable": {
          "cmd": "echo 'Hello'"
        }
      }
    ]
  }
}
"""
    assert out == expected_out
