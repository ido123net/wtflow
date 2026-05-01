from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable
from uuid import UUID, uuid4

from wtflow.infra.artifact import Artifact


@dataclass(frozen=True)
class Node:
    name: str
    command: str | None = None
    timeout: float | None = None
    artifacts: Iterable[Artifact] = field(default_factory=set, hash=False)
    _id: UUID = field(default_factory=uuid4, repr=False)


@dataclass(frozen=True)
class TreeNode(Node):
    children: Iterable[TreeNode] = field(default_factory=tuple, hash=False)

    @property
    def all_artifacts(self) -> set[Artifact]:
        return set(self.artifacts) | {Artifact("stdout"), Artifact("stderr")}
