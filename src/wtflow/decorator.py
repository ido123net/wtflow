from __future__ import annotations

from typing import Callable, Iterable

import wtflow

_ALL_WORKFLOWS: dict[str, wtflow.Workflow] = {}


def wf(
    func: Callable[[], wtflow.Node | Iterable[wtflow.Node]] | None = None,
    *,
    name: str | None = None,
) -> Callable[[Callable[[], wtflow.Node]], None] | None:
    def decorator(func: Callable[[], wtflow.Node | Iterable[wtflow.Node]]) -> None:
        res = func()
        if isinstance(res, wtflow.Node):
            wf_name = name or res.name
            _add_workflow(res, wf_name)
        else:
            for root_node in res:
                wf_name = root_node.name
                _add_workflow(root_node, wf_name)

    def _add_workflow(root_node: wtflow.Node, wf_name: str) -> None:
        wf = wtflow.Workflow(wf_name, root_node)
        if wf_name in _ALL_WORKFLOWS:
            raise RuntimeError(f"Workflow with name '{wf_name}' already exists.")
        _ALL_WORKFLOWS[wf_name] = wf

    if func is not None:
        decorator(func)

    return decorator
