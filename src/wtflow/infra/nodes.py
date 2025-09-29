from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from wtflow.infra.executables import Executable
    from wtflow.infra.executors import Result
    from wtflow.infra.workflow import Workflow

logger = logging.getLogger(__name__)


@dataclass
class Node:
    name: str
    executable: Executable | None = None
    parallel: bool = False
    children: list[Node] = field(default_factory=list)
    result: Result | None = field(default=None)

    _lft: int | None = field(default=None, repr=False)
    _rgt: int | None = field(default=None, repr=False)

    @property
    def id(self) -> str:
        return str(self._id) if hasattr(self, "_id") else self.name

    def set_workflow(self, workflow: Workflow) -> None:
        self._workflow = workflow

    @property
    def fail(self) -> bool:
        return self.result is not None and self.result.retcode != 0
