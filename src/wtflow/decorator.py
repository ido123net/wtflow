from __future__ import annotations

from typing import Callable

import wtflow

_ALL_WORKFLOWS = set()


def workflow(name: str | None = None) -> Callable[[Callable[[], wtflow.Node]], wtflow.Workflow]:
    def decorator(func: Callable[[], wtflow.Node]) -> wtflow.Workflow:
        wf_name = name or func.__name__.replace("_", "-")

        wf = wtflow.Workflow(wf_name, func())
        if wf_name in _ALL_WORKFLOWS:
            raise RuntimeError(f"Workflow with name '{wf_name}' already exists.")
        _ALL_WORKFLOWS.add(wf_name)
        return wf

    return decorator
