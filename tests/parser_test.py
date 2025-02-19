import pathlib

import pytest
from pydantic import ValidationError

from wtflow.nodes import Node
from wtflow.parser import parse_yaml
from wtflow.workflow import Workflow


def test_parse_yaml(file_path: pathlib.Path):
    workflow = parse_yaml(file_path)
    workflow_obj = Workflow(
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
    assert workflow.model_dump() == workflow_obj.model_dump()


def test_parse_yaml_invalid(tmp_path: pathlib.Path):
    file_path = tmp_path / "test.yaml"
    with open(file_path, "w") as file:
        file.write("invalid")
    with pytest.raises(ValidationError):
        parse_yaml(file_path)
