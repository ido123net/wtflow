from __future__ import annotations

from typing import Callable, Iterable

import wtflow

_ALL_WORKFLOWS: dict[str, wtflow.TreeWorkflow] = {}


def wf(
    func: Callable[[], wtflow.TreeWorkflow | wtflow.TreeNode | Iterable[wtflow.TreeNode]] | None = None,
    *,
    name: str | None = None,
) -> Callable[[Callable[[], wtflow.TreeNode]], None]:
    def decorator(func: Callable[[], wtflow.TreeWorkflow | wtflow.TreeNode | Iterable[wtflow.TreeNode]]) -> None:
        res = func()
        if isinstance(res, wtflow.TreeWorkflow):
            _add_workflow(res)
        elif isinstance(res, wtflow.TreeNode):
            wf_name = name or func.__name__.replace("_", "-")
            wf = wtflow.TreeWorkflow(name=wf_name, root=res)
            _add_workflow(wf)
        else:
            wf_name = name or func.__name__.replace("_", "-")
            root_node = wtflow.TreeNode(name=wf_name, children=tuple(res))
            wf = wtflow.TreeWorkflow(name=wf_name, root=root_node)
            _add_workflow(wf)

    def _add_workflow(wf: wtflow.TreeWorkflow) -> None:
        if wf.name in _ALL_WORKFLOWS:
            raise RuntimeError(f"Workflow with name '{wf.name}' already exists.")
        _ALL_WORKFLOWS[wf.name] = wf

    if func is not None:
        decorator(func)

    return decorator
