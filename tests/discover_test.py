import pytest

from wtflow.discover import discover_root_nodes


@pytest.fixture()
def wtflie(tmp_path):
    p = tmp_path / "wtfile.py"
    with open(p, "w") as f:
        f.write('''\
import wtflow


@wtflow.workflow("hello-world")
def workflow_1():
    """A simple workflow that prints Hello World"""
    return wtflow.Node(
        name="Root Node",
        executable=wtflow.Command("echo 'Hello, World!'"),
    )
''')
    return p


@pytest.fixture()
def invalid_wtflie(tmp_path):
    p = tmp_path / "wtfile.py"
    with open(p, "w") as f:
        f.write("""\
import wtflow


@wtflow.workflow(name="test_workflow")
def _():
    return wtflow.Node("")

@wtflow.workflow(name="test_workflow")
def _():
    return wtflow.Node("")
""")
    return p


def test_discover_root_nodes(wtflie):
    root_nodes_dict = discover_root_nodes(wtflie)
    assert len(root_nodes_dict) == 1
    assert "hello-world" in root_nodes_dict


def test_discover_from_directory(wtflie):
    root_nodes_dict = discover_root_nodes(wtflie.parent)
    assert len(root_nodes_dict) == 1
    assert "hello-world" in root_nodes_dict


def test_file_not_exists():
    with pytest.raises(FileNotFoundError):
        discover_root_nodes("/path/not/exist.py")


def test_duplicate_workflow_name(invalid_wtflie):
    with pytest.raises(RuntimeError):
        discover_root_nodes(invalid_wtflie)
