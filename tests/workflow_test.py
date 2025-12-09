from wtflow import Artifact
from wtflow.infra.nodes import Node
from wtflow.infra.workflow import Workflow


def test_serialize():
    wf = Workflow(name="test", root=Node(name="root", artifacts=[Artifact(name="artifact")]))
    assert Workflow.from_dict(wf.to_dict()) == wf
