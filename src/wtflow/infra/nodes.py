from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field

from wtflow.infra.artifact import Artifact


@dataclass(frozen=True)
class Node:
    name: str
    command: str | None = None
    timeout: float | None = None
    artifacts: tuple[Artifact, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class TreeNode(Node):
    children: Iterable[TreeNode] = field(default_factory=tuple, hash=False)
