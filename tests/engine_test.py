import os

import pytest

from wtflow.config import NO_CONFIG, Config, LocalStorageConfig, Sqlite3Config
from wtflow.infra.engine import Engine
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


@pytest.mark.asyncio
async def test_run():
    wf = Workflow(
        name="test run",
        root=Node(
            name="Root Node",
            children=[
                Node(name="Node 1", command='echo "Hello 1"'),
                Node(
                    name="Node 2",
                    parallel=True,
                    children=[
                        Node(name="Node 2.1", command='echo "World 2.1"'),
                        Node(name="Node 2.2", command='echo "World 2.2"'),
                    ],
                ),
            ],
        ),
    )
    engine = Engine()
    await engine.run_workflow(wf)


@pytest.mark.asyncio
async def test_fail_run(capfd):
    wf = Workflow(
        name="test fail run",
        root=Node(
            name="fail node",
            command="command-not-exist",
        ),
    )
    engine = Engine()
    assert await engine.run_workflow(wf) == 1
    root_node_result = engine.get_workflow_executor(wf).node_result(wf.root)
    assert root_node_result != 0
    _, err = capfd.readouterr()
    assert "not found" in err


@pytest.mark.asyncio
async def test_stop_on_failure():
    wf = Workflow(
        name="test stop on failure",
        root=Node(
            name="Root Node",
            children=[
                Node(name="Node 1", command='echo "Hello 1"'),
                Node(
                    name="Node 2",
                    parallel=True,
                    children=[
                        Node(name="Node 2.1", command='echo "World 2.1"'),
                        Node(name="Node 2.2", command="command-not-exist"),
                    ],
                ),
                Node(name="Node 3", command='echo "Hello 3"'),
            ],
        ),
    )
    engine = Engine(config=Config())
    assert await engine.run_workflow(wf) == 1
    node_result = engine.get_workflow_executor(wf).node_result(wf.root.children[2])
    assert node_result is None


@pytest.mark.asyncio
async def test_with_db_config(db_config):
    config = Config(database=db_config)
    wf = Workflow(
        name="test with db config",
        root=Node(
            name="Root Node",
            children=[
                Node(name="Node 1", command="echo 'Hello'"),
            ],
        ),
    )
    engine = Engine(config=config)
    assert await engine.run_workflow(wf) == 0


@pytest.mark.asyncio
async def test_with_storage_config(local_storage_config, data_dir):
    config = Config(storage=local_storage_config)
    wf = Workflow(
        name="test no db",
        root=Node(
            name="Root Node",
            children=[
                Node(name="Node 1", command="echo 'Hello'"),
            ],
        ),
    )
    engine = Engine(config=config)
    assert await engine.run_workflow(wf) == 0
    log_path = data_dir / "test no db" / "Node 1" / "stdout.txt"
    assert log_path.exists()
    assert log_path.read_text() == "Hello\n"


@pytest.mark.asyncio
async def test_with_db_and_storage_config(db_config, local_storage_config):
    config = Config(database=db_config, storage=local_storage_config)
    wf = Workflow(
        name="test with db",
        root=Node(
            name="Root Node",
            children=[
                Node(name="Node 1", command="echo 'Hello'"),
            ],
        ),
    )
    engine = Engine(config=config)
    assert await engine.run_workflow(wf) == 0
