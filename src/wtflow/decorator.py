from __future__ import annotations

from typing import Callable, Iterable

from wtflow.infra.nodes import TreeNode
from wtflow.infra.workflow import Tree

_ALL_WORKFLOWS: dict[str, Tree] = {}


def wf(
    func: Callable[[], Tree | TreeNode | Iterable[TreeNode]] | None = None,
    *,
    name: str | None = None,
) -> Callable[[Callable[[], TreeNode]], None]:
    def decorator(func: Callable[[], Tree | TreeNode | Iterable[TreeNode]]) -> None:
        res = func()
        if isinstance(res, Tree):
            _add_workflow(res)
        elif isinstance(res, TreeNode):
            wf_name = name or func.__name__.replace("_", "-")
            wf = Tree(name=wf_name, root=res)
            _add_workflow(wf)
        else:
            wf_name = name or func.__name__.replace("_", "-")
            root_node = TreeNode(name=wf_name, children=tuple(res))
            wf = Tree(name=wf_name, root=root_node)
            _add_workflow(wf)

    def _add_workflow(wf: Tree) -> None:
        if wf.name in _ALL_WORKFLOWS:
            raise RuntimeError(f"Workflow with name '{wf.name}' already exists.")
        _ALL_WORKFLOWS[wf.name] = wf

    if func is not None:
        decorator(func)

    return decorator
