from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable


@dataclass(frozen=True)
class Node:
    name: str
    command: str | None = None
    timeout: float | None = None
    parallel: bool = False
    children: Iterable[Node] = field(default_factory=tuple, hash=False)
