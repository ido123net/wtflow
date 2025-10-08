import pytest

from wtflow.cli import _cmd_list, _cmd_run, main


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
        executable=wtflow.Command("echo 'Hello, World!'"),
    )


@wtflow.wf
def workflow_2():
    return wtflow.Node(
        name="workflow-2",
        executable=wtflow.Command("echo 'Workflow 2'"),
    )
""")
    return p


WTFLIE_OUT = """\
Found 2 workflow(s):
- hello-world
- workflow-2
"""


def test_list(wtfile, capsys):
    main(["--file", str(wtfile), "list"])
    out, _ = capsys.readouterr()
    assert out == WTFLIE_OUT


def test_run_all(wtfile, capsys, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    main(["--file", str(wtfile), "run"])
    out, _ = capsys.readouterr()
    expected_out = """\
Hello, World!
Workflow 2
"""
    assert out == expected_out


def test_run_workflow(wtfile, capsys, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    main(["--file", str(wtfile), "run", "--workflow", "hello-world"])
    out, _ = capsys.readouterr()
    assert out == "Hello, World!\n"


def test_with_config(wtfile, ini_config, capsys):
    main(["--config", str(ini_config), "--file", str(wtfile), "run", "--workflow", "hello-world"])
    out, _ = capsys.readouterr()
    assert out == ""


def test_ignore_config(wtfile, ini_config, tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    main(["--file", str(wtfile), "--no-config", "run", "--workflow", "hello-world"])
    out, _ = capsys.readouterr()
    assert out == "Hello, World!\n"


def test_file_not_exist(capsys):
    res = main(["--file", "/does/not/exist.py", "list"])
    assert res == 1
    _, err = capsys.readouterr()
    assert err == "Error: The specified workflows path '/does/not/exist.py' does not exist.\n"


def test_no_file(monkeypatch, tmp_path, wtfile, capsys):
    monkeypatch.chdir(tmp_path)
    res = main(["list"])
    assert res == 0
    out, _ = capsys.readouterr()
    assert out == WTFLIE_OUT


def test_no_workflow_list(capsys):
    res = _cmd_list({})
    assert res == 0
    out, _ = capsys.readouterr()
    assert out == "No workflows found.\n"


def test_no_workflow_run(capsys):
    res = _cmd_run({})
    assert res == 1
    _, err = capsys.readouterr()
    assert err == "No workflows found.\n"


def test_workflow_not_found(capsys):
    res = _cmd_run({"workflow-1": None}, "workflow-2")
    assert res == 1
    _, err = capsys.readouterr()
    assert err == "Error: Workflow 'workflow-2' not found.\n"
