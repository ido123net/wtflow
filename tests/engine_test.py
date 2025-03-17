import time

from wtflow.artifact import Artifact
from wtflow.engine import Engine
from wtflow.executables import Command, PyFunc
from wtflow.nodes import Node
from wtflow.workflow import Workflow


def test_run():
    wf = Workflow(
        name="Test Workflow",
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
        name="Test Workflow",
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
        name="Test Workflow",
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
        name="Test Workflow",
        root=Node(
            name="Root Node",
            executable=Command(cmd="sleep 5", timeout=1),
        ),
    )
    engine = Engine(wf)
    assert engine.run() == 1


def func(*args, **kwargs):
    print(args, kwargs)


def test_PyFunc_executable():
    wf = Workflow(
        name="Test Workflow",
        root=Node(
            name="Root Node",
            executable=PyFunc(func, args=(1, 2), kwargs={"a": 1}),
        ),
    )
    engine = Engine(wf)
    assert engine.run() == 0
    assert engine.workflow.root.stdout == b"(1, 2) {'a': 1}\n"
    assert engine.workflow.root.stderr == b""


def f_sleep():
    time.sleep(2)
    raise Exception("fail")


def test_PyFunc_timeout():
    wf = Workflow(
        name="Test Workflow",
        root=Node(
            name="Root Node",
            executable=PyFunc(f_sleep, timeout=1),
        ),
    )
    engine = Engine(wf)
    assert engine.run() == 1


def test_PyFunc_exeption():
    wf = Workflow(
        name="Test Workflow",
        root=Node(
            name="Root Node",
            executable=PyFunc(func=f_sleep),
        ),
    )
    engine = Engine(wf)
    assert engine.run() == 1


def test_partial_stdout():
    wf = Workflow(
        name="Test Workflow",
        root=Node(
            name="Root Node",
            executable=Command(cmd="echo 'Hello' && sleep 2 && echo 'World'", timeout=1),
        ),
    )
    engine = Engine(wf)
    engine.run()
    assert engine.workflow.root.stdout == b"Hello\n"


def test_continue_on_failure():
    wf = Workflow(
        name="Test Workflow",
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


def test_artifact(tmp_path):
    file_path = tmp_path / "test.txt"
    artifact = Artifact("test", file_path=file_path)
    wf = Workflow(
        name="Test Workflow",
        root=Node(
            name="Root Node",
            executable=Command(cmd=f"echo 'Hello' > {artifact.path}"),
            artifacts=[artifact],
        ),
    )
    enine = Engine(wf)
    assert enine.run() == 0
    assert artifact.data == b"Hello\n"
