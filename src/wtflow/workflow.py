from __future__ import annotations

from dataclasses import dataclass

from wtflow.nodes import Node


@dataclass
class Workflow:
    name: str
    root: Node
