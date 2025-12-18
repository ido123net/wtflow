from __future__ import annotations

import logging
from dataclasses import dataclass, field
from uuid import uuid4

from wtflow.infra.executables import Command

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Node:
    name: str
    executable: Command | None = None
    parallel: bool = False
    children: list[Node] = field(default_factory=list)
    id: str = field(default_factory=lambda: uuid4().hex, repr=False, init=False)

    def __hash__(self) -> int:
        return hash(self.id)
