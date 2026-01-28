from __future__ import annotations

from typing import Callable, Iterable

import wtflow

_ALL_WORKFLOWS: dict[str, wtflow.Workflow] = {}


def wf(
    func: Callable[[], wtflow.Workflow | wtflow.Node | Iterable[wtflow.Node]] | None = None,
    *,
    name: str | None = None,
) -> Callable[[Callable[[], wtflow.Node]], None]:
    def decorator(func: Callable[[], wtflow.Workflow | wtflow.Node | Iterable[wtflow.Node]]) -> None:
        res = func()
        if isinstance(res, wtflow.Workflow):
            _add_workflow(res)
        elif isinstance(res, wtflow.Node):
            wf_name = name or func.__name__.replace("_", "-")
            wf = wtflow.Workflow(name=wf_name, root=res)
            _add_workflow(wf)
        else:
            wf_name = name or func.__name__.replace("_", "-")
            root_node = wtflow.Node(name=wf_name, children=tuple(res))
            wf = wtflow.Workflow(name=wf_name, root=root_node)
            _add_workflow(wf)

    def _add_workflow(wf: wtflow.Workflow) -> None:
        if wf.name in _ALL_WORKFLOWS:
            raise RuntimeError(f"Workflow with name '{wf.name}' already exists.")
        _ALL_WORKFLOWS[wf.name] = wf

    if func is not None:
        decorator(func)

    return decorator
