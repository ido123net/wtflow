import pytest

from wtflow.decorator import workflow


def test_override_workflow():
    with pytest.raises(RuntimeError):

        @workflow(name="test_workflow")
        def _(): ...

        @workflow(name="test_workflow")
        def _(): ...
