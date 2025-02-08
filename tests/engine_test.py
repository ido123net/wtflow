import time

import pytest

from wtflow.engine import Engine
from wtflow.nodes import Node, PyFunc
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
            stop_on_failure=False,
        ),
    )
    engine = Engine(wf)
    assert await engine.run() == 0
    assert engine.workflow.root.outcome == "timeout"


def func(*args, **kwargs):
    print(args, kwargs)


@pytest.mark.parametrize(
    "func",
    (func, "tests.engine_test.func"),
)
async def test_PyFunc_executable(func):
    wf = Workflow(
        name="Test Workflow",
        root=Node(
            name="Root Node",
            executable=PyFunc(
                func=func,
                args=(1, 2),
                kwargs={"a": 1},
            ),
        ),
    )
    engine = Engine(wf)
    await engine.run()
    assert engine.workflow.root.outcome == "success"
    assert engine.workflow.root.result.retcode == 0
    assert engine.workflow.root.result.stdout == b"(1, 2) {'a': 1}\n"
    assert engine.workflow.root.result.stderr == b""


def f_sleep():
    time.sleep(2)
    raise Exception("fail")


async def test_PyFunc_timeout():
    wf = Workflow(
        name="Test Workflow",
        root=Node(
            name="Root Node",
            executable=PyFunc(func=f_sleep),
            timeout=1,
        ),
    )
    engine = Engine(wf)
    assert await engine.run() == 1
    assert engine.workflow.root.outcome == "timeout"
    assert engine.workflow.root.result is None


async def test_PyFunc_exeption():
    wf = Workflow(
        name="Test Workflow",
        root=Node(
            name="Root Node",
            executable=PyFunc(
                func=f_sleep,
            ),
        ),
    )
    engine = Engine(wf)
    assert await engine.run() == 1
    assert engine.workflow.root.outcome == "failure"
    assert engine.workflow.root.result.retcode == 1
    assert b"fail" in engine.workflow.root.result.stderr


async def test_cmd_or_executable():
    with pytest.raises(ValueError) as exc:
        Workflow(
            name="Test Workflow",
            root=Node(
                name="Root Node",
                cmd="echo 'Hello'",
                executable=PyFunc(func=f_sleep),
            ),
        )
    assert "`cmd` and `executable` are mutually exclusive" in str(exc.value)
