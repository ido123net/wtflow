import pytest

YAML_CONTENT = """\
name: Test Workflow
root:
  name: Root Node
  children:
    - name: Node 1
      cmd: echo "Hello 1"
    - name: Node 2
      parallel: true
      children:
        - name: Node 2.1
          cmd: echo "World 2.1"
        - name: Node 2.2
          cmd: echo "World 2.2"
"""


@pytest.fixture(scope="module")
def file_path(tmp_path_factory: pytest.TempPathFactory):
    tmp_path = tmp_path_factory.mktemp("data")
    file_path = tmp_path / "test.yaml"
    with open(file_path, "w") as file:
        file.write(YAML_CONTENT)
    return file_path
