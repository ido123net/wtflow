from __future__ import annotations

import logging
from dataclasses import dataclass, field
from uuid import uuid4

from wtflow.executables import Executable
from wtflow.executors import Result

logger = logging.getLogger(__name__)


@dataclass
class Node:
    name: str
    executable: Executable | None = None
    result: Result | None = None
    parallel: bool = False
    children: list[Node] = field(default_factory=list)

    _node_id: str = field(default_factory=lambda: str(uuid4().hex), repr=False)
    _parent: Node | None = field(default=None, repr=False)

    def __post_init__(self) -> None:
        if self.children:
            for child in self.children:
                child._parent = self

    @property
    def parent(self) -> Node | None:
        return self._parent  # pragma: no cover

    def execute(self) -> None:
        if self.executable:
            logger.debug(f"Executing Node {self.name}: ({self.executable = })")
            self.result = self.executable.run()
            logger.debug(f"Node {self.name} ({self.result = })")
