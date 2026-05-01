from __future__ import annotations

from dataclasses import dataclass, field
from uuid import UUID, uuid4

from wtflow.infra.nodes import Node


@dataclass(frozen=True)
class Workflow:
    name: str
    root: Node
    _id: UUID = field(default_factory=uuid4)
