import time

import pytest

from wtflow.config import Config
from wtflow.infra.engine import Engine, ExitCode
from wtflow.infra.nodes import Node, TreeNode
from wtflow.infra.workflow import Graph, Tree


@pytest.mark.asyncio
async def test_run():
    wf = Tree(
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
    with Engine() as engine:
        await engine.run_workflow(wf)


@pytest.mark.asyncio
async def test_fail_run(capfd):
    wf = Tree(
        name="test fail run",
        root=TreeNode(
            name="fail node",
            command="command-not-exist",
        ),
    )
    with Engine() as engine:
        assert await engine.run_workflow(wf) == ExitCode.FAIL
    _, err = capfd.readouterr()
    assert "not found" in err


@pytest.mark.asyncio
async def test_stop_on_failure(capfdbinary):
    wf = Tree(
        name="test stop on failure",
        root=TreeNode(
            name="Root Node",
            children=[
                TreeNode(name="Node 1", command='echo "Hello 1"'),
                TreeNode(
                    name="Node 2",
                    children=[
                        TreeNode(name="Node 2.1", command='echo "World 2.1"'),
                        TreeNode(name="Node 2.2", command="sleep 0.01 && command-not-exist"),
                        TreeNode(name="Node 2.3", command='echo "EXISTS" && sleep 1 && echo "NOPE"'),
                    ],
                ),
                TreeNode(name="Node 3", command='echo "Hello 3"'),
            ],
        ),
    )
    with Engine(config=Config()) as engine:
        assert await engine.run_workflow(wf) == ExitCode.FAIL
    out, _ = capfdbinary.readouterr()
    assert b"EXISTS" in out
    assert b"NOPE" not in out


@pytest.mark.asyncio
async def test_timeout_node(capfdbinary):
    wf = Tree(
        name="test timeout node",
        root=TreeNode(
            name="Root Node",
            command="echo 'Hello' && sleep 1 && echo 'World'",
            timeout=0.1,
        ),
    )
    start_time = time.perf_counter()
    with Engine(config=Config()) as engine:
        assert await engine.run_workflow(wf) == ExitCode.FAIL
    elapsed = time.perf_counter() - start_time
    assert elapsed < 0.2
    stdout, stderr = capfdbinary.readouterr()
    assert stdout == b"Hello\n"
    assert stderr == b""


@pytest.mark.asyncio
async def test_with_storage_config(local_storage_config, data_dir):
    config = Config(storage=local_storage_config)
    wf = Tree(
        name="test no db",
        root=TreeNode(
            name="Root Node",
            children=[
                TreeNode(name="Node 1", command="echo 'Hello' && echo 'world'"),
            ],
        ),
    )
    with Engine(config=config) as engine:
        assert await engine.run_workflow(wf) == 0
    log_path = data_dir / "test no db" / "Node 1" / "stdout.txt"
    assert log_path.exists()
    assert log_path.read_text() == "Hello\nworld\n"


@pytest.mark.asyncio
async def test_long_with_short(capfdbinary):
    n1 = Node(name="n1", command="echo 1")
    n2 = Node(name="n2", command="sleep 0.1 && echo 2")
    n3 = Node(name="n3", command="sleep 0.01 && echo 3")
    n4 = Node(name="n4", command="echo 4")
    graph = Graph(
        name="test_long_with_short",
        nodes=(n1, n2, n3, n4),
        edges=(
            (n1, n2),
            (n1, n3),
            (n3, n4),
        ),
    )
    with Engine(config=Config()) as engine:
        await engine.run_graph(graph)
    stdout, stderr = capfdbinary.readouterr()
    assert stderr == b""
    assert stdout == b"1\n3\n4\n2\n"
