import pytest

import wtflow


def test_override_workflow():
    with pytest.raises(RuntimeError):

        @wtflow.workflow(name="test_workflow")
        def _():
            return wtflow.Node("")

        @wtflow.workflow(name="test_workflow")
        def _():
            return wtflow.Node("")
