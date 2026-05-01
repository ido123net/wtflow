from __future__ import annotations

from dataclasses import dataclass, field
from uuid import UUID, uuid4

from wtflow.infra.nodes import TreeNode


@dataclass(frozen=True)
class TreeWorkflow:
    name: str
    root: TreeNode
    _id: UUID = field(default_factory=uuid4, repr=False)
