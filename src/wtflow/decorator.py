from __future__ import annotations

from typing import Callable

from wtflow.infra.nodes import Node

ROOT_NODES: dict[str, Node] = {}


def workflow(name: str | None = None) -> Callable[[Callable[[], Node]], None]:
    def decorator(func: Callable[[], Node]) -> None:
        workflow_name = name or func.__name__.replace("_", "-")

        if workflow_name in ROOT_NODES:
            raise RuntimeError(f'Workflow with name "{workflow_name}" already exists.')

        ROOT_NODES[workflow_name] = func()

    return decorator
