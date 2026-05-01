import sqlite3
import time
from contextlib import closing

import pytest

from wtflow.config import Config, LocalStorageConfig, Sqlite3Config
from wtflow.infra.engine import Engine
from wtflow.infra.executors import NodeResult
from wtflow.infra.nodes import TreeNode
from wtflow.infra.workflow import TreeWorkflow

schema_sql = """\
CREATE TABLE IF NOT EXISTS workflows (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    result INTEGER NULL,
    name TEXT NOT NULL
) STRICT;

CREATE TABLE IF NOT EXISTS nodes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    command TEXT NULL,
    workflow_id TEXT NOT NULL,
    FOREIGN KEY (workflow_id) REFERENCES workflows (id) ON DELETE CASCADE
) STRICT;

CREATE TABLE IF NOT EXISTS artifacts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    node_id INTEGER NOT NULL,
    FOREIGN KEY (node_id) REFERENCES nodes (id) ON DELETE CASCADE
) STRICT;

CREATE TABLE IF NOT EXISTS executions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    start_at TEXT NULL,
    end_at TEXT NULL,
    result INTEGER NULL,
    node_id INTEGER NOT NULL,
    FOREIGN KEY (node_id) REFERENCES nodes (id) ON DELETE CASCADE
) STRICT;

-- Indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_nodes_workflow_id ON nodes (workflow_id);
CREATE INDEX IF NOT EXISTS idx_executions_node_id ON executions (node_id);
"""


@pytest.fixture()
def data_dir(tmp_path_factory):
    data_dir = tmp_path_factory.mktemp("data")
    return data_dir


@pytest.fixture()
def db_config(data_dir):
    database_path = f"{data_dir}/test.db"
    config = Sqlite3Config(database_path=database_path)
    with closing(sqlite3.connect(config.database_path)) as conn:
        conn.executescript(schema_sql)
    return config


@pytest.fixture()
def local_storage_config(data_dir):
    return LocalStorageConfig(base_path=data_dir)


@pytest.mark.asyncio
async def test_run():
    wf = TreeWorkflow(
        name="test run",
        root=TreeNode(
            name="Root Node",
            children=[
                TreeNode(name="Node 1", command='echo "Hello 1"'),
                TreeNode(
                    name="Node 2",
                    children=[
                        TreeNode(name="Node 2.1", command='echo "World 2.1"'),
                        TreeNode(name="Node 2.2", command='echo "World 2.2"'),
                    ],
                ),
            ],
        ),
    )
    engine = Engine()
    await engine.run_workflow(wf)


@pytest.mark.asyncio
async def test_fail_run(capfd):
    wf = TreeWorkflow(
        name="test fail run",
        root=TreeNode(
            name="fail node",
            command="command-not-exist",
        ),
    )
    engine = Engine()
    assert await engine.run_workflow(wf) == NodeResult.FAIL
    _, err = capfd.readouterr()
    assert "not found" in err


@pytest.mark.asyncio
async def test_stop_on_failure(capfdbinary):
    wf = TreeWorkflow(
        name="test stop on failure",
        root=TreeNode(
            name="Root Node",
            children=[
                TreeNode(name="Node 1", command='echo "Hello 1"'),
                TreeNode(
                    name="Node 2",
                    children=[
                        TreeNode(name="Node 2.1", command='echo "World 2.1"'),
                        TreeNode(name="Node 2.2", command="command-not-exist"),
                        TreeNode(name="Node 2.3", command='echo "EXISTS" && sleep 1 && echo "NOPE"'),
                    ],
                ),
                TreeNode(name="Node 3", command='echo "Hello 3"'),
            ],
        ),
    )
    engine = Engine(config=Config())
    assert await engine.run_workflow(wf) == NodeResult.CHILD_FAILED
    out, _ = capfdbinary.readouterr()
    assert b"EXISTS" in out
    assert b"NOPE" not in out


@pytest.mark.asyncio
async def test_timeout_node(capfdbinary):
    wf = TreeWorkflow(
        name="test timeout node",
        root=TreeNode(
            name="Root Node",
            command="echo 'Hello' && sleep 1 && echo 'World'",
            timeout=0.1,
        ),
    )
    engine = Engine(Config())
    start_time = time.perf_counter()
    assert await engine.run_workflow(wf) == NodeResult.TIMEOUT
    elapsed = time.perf_counter() - start_time
    assert elapsed < 0.2
    stdout, stderr = capfdbinary.readouterr()
    assert stdout == b"Hello\n"
    assert stderr == b""


@pytest.mark.asyncio
async def test_with_db_config(db_config):
    config = Config(database=db_config)
    wf = TreeWorkflow(
        name="test with db config",
        root=TreeNode(
            name="Root Node",
            children=[
                TreeNode(name="Node 1", command="echo 'Hello'"),
            ],
        ),
    )
    engine = Engine(config=config)
    assert await engine.run_workflow(wf) == 0


@pytest.mark.asyncio
async def test_with_storage_config(local_storage_config, data_dir):
    config = Config(storage=local_storage_config)
    wf = TreeWorkflow(
        name="test no db",
        root=TreeNode(
            name="Root Node",
            children=[
                TreeNode(name="Node 1", command="echo 'Hello' && echo 'world'"),
            ],
        ),
    )
    engine = Engine(config=config)
    assert await engine.run_workflow(wf) == 0
    log_path = data_dir / "test no db" / "Node 1" / "stdout.txt"
    assert log_path.exists()
    assert log_path.read_text() == "Hello\nworld\n"


@pytest.mark.asyncio
async def test_with_db_and_storage_config(db_config, local_storage_config):
    config = Config(database=db_config, storage=local_storage_config)
    wf = TreeWorkflow(
        name="test with db",
        root=TreeNode(
            name="Root Node",
            children=[
                TreeNode(name="Node 1", command="echo 'Hello'"),
            ],
        ),
    )
    engine = Engine(config=config)
    assert await engine.run_workflow(wf) == 0
