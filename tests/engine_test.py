import pytest
from wtflow.engine import Engine
from wtflow.nodes import Node
from wtflow.workflow import Workflow

pytestmark = pytest.mark.asyncio(loop_scope="module")


async def test_run():
    wf = Workflow(
        name="Test Workflow",
        root=Node(
            name="Root Node",
            children=[
                Node(name="Node 1", cmd='echo "Hello 1"'),
                Node(
                    name="Node 2",
                    parallel=True,
                    children=[
                        Node(name="Node 2.1", cmd='echo "World 2.1"'),
                        Node(name="Node 2.2", cmd='echo "World 2.2"'),
                    ],
                ),
            ],
        ),
    )
    engine = Engine(wf)
    await engine.run()


async def test_fail_run():
    wf = Workflow(
        name="Test Workflow",
        root=Node(
            name="fail node",
            cmd="command-not-exist",
            stop_on_failure=True,
        ),
    )
    engine = Engine(wf)
    assert await engine.run() == 1
    assert b"not found" in engine.workflow.root.result.stderr
    assert engine.workflow.root.outcome == "failure"


async def test_stop_on_failure():
    wf = Workflow(
        name="Test Workflow",
        root=Node(
            name="Root Node",
            children=[
                Node(name="Node 1", cmd='echo "Hello 1"'),
                Node(
                    name="Node 2",
                    parallel=True,
                    children=[
                        Node(name="Node 2.1", cmd='echo "World 2.1"'),
                        Node(name="Node 2.2", cmd="command-not-exist", stop_on_failure=True),
                    ],
                ),
                Node(name="Node 3", cmd='echo "Hello 3"'),
            ],
        ),
    )
    engine = Engine(wf)
    assert await engine.run() == 1
    assert engine.workflow.root.children[1].children[1].outcome == "failure"
    assert engine.workflow.root.children[1].outcome == "stopped"
    assert engine.workflow.root.outcome == "stopped"


async def test_timeout_stop():
    wf = Workflow(
        name="Test Workflow",
        root=Node(
            name="Root Node",
            timeout=1,
            cmd="sleep 5",
            stop_on_failure=True,
        ),
    )
    engine = Engine(wf)
    assert await engine.run() == 1
    assert engine.workflow.root.outcome == "timeout"


async def test_timeout_continue():
    wf = Workflow(
        name="Test Workflow",
        root=Node(
            name="Root Node",
            timeout=1,
            cmd="sleep 5",
        ),
    )
    engine = Engine(wf)
    assert await engine.run() == 0
    assert engine.workflow.root.outcome == "timeout"
