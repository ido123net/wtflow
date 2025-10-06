import pytest

import wtflow


def test_override_workflow():
    with pytest.raises(RuntimeError):

        @wtflow.wf(name="test_wf")
        def _():
            return wtflow.Node("")

        @wtflow.wf(name="test_wf")
        def _():
            return wtflow.Node("")
