from __future__ import annotations

import pytest

from wtflow.infra.artifact import Artifact
from wtflow.infra.nodes import Node


@pytest.mark.parametrize("artifact_name", ["stdout", "stderr"])
def test_reserved_artifact(artifact_name):
    with pytest.raises(ValueError) as excinfo:
        Node(name="test", artifacts=[Artifact(name=artifact_name)])

    assert str(excinfo.value) == "`stdout` and `stderr` are reserved artifact names"
