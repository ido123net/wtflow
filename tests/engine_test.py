import os

import pytest

from wtflow.config import NO_CONFIG, Config, LocalStorageConfig, RunConfig, Sqlite3Config
from wtflow.infra.engine import Engine
from wtflow.infra.executables import Command, PyFunc
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
    assert b"not found" in engine.workflow.root.result.stderr


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
    engine = Engine(wf, config=Config())
    assert engine.run() == 1
    assert engine.workflow.root.children[2].result is None


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
    assert engine.workflow.root.children[1].result.stdout == b"run anyway\n"


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
    engine = Engine(wf, config=config)
    assert engine.run() == 0


def test_with_storage_config(local_storage_config):
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
    engine = Engine(wf, config=config)
    assert engine.run() == 0


def test_with_db_and_storage_config(db_config, local_storage_config):
    config = Config(database=db_config, storage=local_storage_config)
    wf = Workflow(
        name="test no db",
        root=Node(
            name="Root Node",
            children=[
                Node(name="Node 1", executable=Command(cmd="echo 'Hello'")),
            ],
        ),
    )
    engine = Engine(wf, config=config)
    assert engine.run() == 0


def func(*args, **kwargs): ...


def test_dry_run(capsys):
    wf = Workflow(
        name="test dry run",
        root=Node(
            name="Root Node",
            children=[
                Node(name="Node 1", executable=Command(cmd="echo 'Hello'")),
                Node(name="Node 2", executable=PyFunc(func=func, args=(1, 2), kwargs={"a": 3})),
            ],
        ),
    )
    engine = Engine(wf, dry_run=True)
    assert engine.run() == 0
    out, _ = capsys.readouterr()
    expected_out = """\
name: test dry run
root:
  name: Root Node
  children:
  - name: Node 1
    executable:
      cmd: echo 'Hello'
  - name: Node 2
    executable:
      func: !!python/name:tests.engine_test.func ''
      args: !!python/tuple
      - 1
      - 2
      kwargs:
        a: 3
"""
    print(out)
    assert out == expected_out
