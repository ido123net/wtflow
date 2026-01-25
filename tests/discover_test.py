import pytest

from wtflow.discover import discover_workflows


@pytest.fixture()
def wtfile(tmp_path):
    p = tmp_path / "wtfile.py"
    with open(p, "w") as f:
        f.write("""\
import wtflow


@wtflow.wf(name="hello-world")
def workflow_1():
    return wtflow.Node(
        name="Root Node",
        executable=wtflow.Command(cmd="echo 'Hello, World!'"),
    )

@wtflow.wf
def hello_world2():
    return [
        wtflow.Node(
            name=f"hello-world-{x}",
            executable=wtflow.Command(cmd="echo hello world"),
        )
        for x in ["1", "2", "3"]
    ]
""")
    return p


@pytest.fixture()
def invalid_wtfile(tmp_path):
    p = tmp_path / "wtfile.py"
    with open(p, "w") as f:
        f.write("""\
import wtflow


@wtflow.wf(name="test_wf")
def _():
    return wtflow.Node(name="")

@wtflow.wf(name="test_wf")
def _():
    return wtflow.Node(name="")
""")
    return p


def test_discover_root_nodes(wtfile):
    root_nodes_dict = discover_workflows(wtfile)
    assert len(root_nodes_dict) == 2
    assert "hello-world" in root_nodes_dict
    wf2 = root_nodes_dict["hello-world2"]
    for i in ["1", "2", "3"]:
        assert f"hello-world-{i}" in {node.name for node in wf2.root.children}


def test_discover_from_directory(wtfile):
    root_nodes_dict = discover_workflows(wtfile.parent)
    assert len(root_nodes_dict) == 2
    assert "hello-world" in root_nodes_dict
    wf2 = root_nodes_dict["hello-world2"]
    for i in ["1", "2", "3"]:
        assert f"hello-world-{i}" in {node.name for node in wf2.root.children}


def test_file_not_exists():
    with pytest.raises(FileNotFoundError):
        discover_workflows("/path/not/exist.py")


def test_duplicate_workflow_name(invalid_wtfile):
    with pytest.raises(RuntimeError):
        discover_workflows(invalid_wtfile)


@pytest.fixture()
def wtfile_workflow(tmp_path):
    p = tmp_path / "wtfile.py"
    with open(p, "w") as f:
        f.write("""\
import wtflow


@wtflow.wf
def run_pytest():
    return wtflow.Workflow(
        name="pytest",
        root=wtflow.Node(
            name="testing supported versions",
            children=[
                wtflow.Node(
                    name=f"pytest-{ver}",
                    executable=wtflow.Command(cmd=f"uv run -p{ver} pytest --cov"),
                )
                for ver in ("3.10", "3.11", "3.12", "3.13", "3.14")
            ],
        ),
    )
""")
    return p


def test_discover_workflow(wtfile_workflow):
    root_nodes_dict = discover_workflows(wtfile_workflow)
    assert "pytest" in root_nodes_dict
