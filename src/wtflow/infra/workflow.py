from __future__ import annotations

from dataclasses import dataclass

from wtflow.infra.nodes import Node


@dataclass(frozen=True)
class Workflow:
    name: str
    root: Node
