from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

from wtflow.infra.artifact import Artifact


@dataclass(frozen=True)
class Node:
    name: str
    command: str | None = None
    timeout: float | None = None
    children: Iterable[Node] = field(default_factory=tuple, hash=False)
    artifacts: Iterable[Artifact] = field(default_factory=set, hash=False)

    @property
    def all_artifacts(self) -> set[Artifact]:
        return set(self.artifacts) | {Artifact("stdout"), Artifact("stderr")}
