import pytest

from wtflow.discover import discover_root_nodes


@pytest.fixture()
def wtflie(tmp_path):
    p = tmp_path / "wtfile.py"
    with open(p, "w") as f:
        f.write("""\
import wtflow


@wtflow.wf(name="hello-world")
def workflow_1():
    return wtflow.Node(
        name="Root Node",
        executable=wtflow.Command("echo 'Hello, World!'"),
    )

@wtflow.wf
def hello_world():
    return [wtflow.Node(f"hello-world-{x}", wtflow.Command("echo hello world")) for x in ["1", "2", "3"]]
""")
    return p


@pytest.fixture()
def invalid_wtflie(tmp_path):
    p = tmp_path / "wtfile.py"
    with open(p, "w") as f:
        f.write("""\
import wtflow


@wtflow.wf(name="test_wf")
def _():
    return wtflow.Node("")

@wtflow.wf(name="test_wf")
def _():
    return wtflow.Node("")
""")
    return p


def test_discover_root_nodes(wtflie):
    root_nodes_dict = discover_root_nodes(wtflie)
    assert len(root_nodes_dict) == 4
    assert "hello-world" in root_nodes_dict
    for i in ["1", "2", "3"]:
        assert f"hello-world-{i}" in root_nodes_dict


def test_discover_from_directory(wtflie):
    root_nodes_dict = discover_root_nodes(wtflie.parent)
    assert len(root_nodes_dict) == 4
    assert "hello-world" in root_nodes_dict
    for i in ["1", "2", "3"]:
        assert f"hello-world-{i}" in root_nodes_dict


def test_file_not_exists():
    with pytest.raises(FileNotFoundError):
        discover_root_nodes("/path/not/exist.py")


def test_duplicate_workflow_name(invalid_wtflie):
    with pytest.raises(RuntimeError):
        discover_root_nodes(invalid_wtflie)
