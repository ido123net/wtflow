from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from wtflow.infra.artifact import Artifact

if TYPE_CHECKING:
    from wtflow.infra.executables import Executable
    from wtflow.infra.executors import Result

logger = logging.getLogger(__name__)


@dataclass
class Node:
    name: str
    executable: Executable | None = None
    parallel: bool = False
    children: list[Node] = field(default_factory=list)
    result: Result | None = field(default=None)
    artifacts: list[Artifact] = field(default_factory=list)

    _stdout: Artifact = field(default_factory=lambda: Artifact(name="stdout"))
    _stderr: Artifact = field(default_factory=lambda: Artifact(name="stderr"))
    _id: int | None = field(default=None, repr=False, init=False)
    _lft: int | None = field(default=None, repr=False, init=False)
    _rgt: int | None = field(default=None, repr=False, init=False)

    @property
    def _artifact_dict(self) -> dict[str, Artifact]:
        return {artifact.name: artifact for artifact in self.all_artifacts}

    @property
    def all_artifacts(self) -> list[Artifact]:
        return [self._stdout, self._stderr] + self.artifacts

    def get_artifact(self, name: str) -> Artifact:
        return self._artifact_dict[name]

    @property
    def id(self) -> str:
        _id = self._id or self.name
        return str(_id)

    @property
    def fail(self) -> bool:
        return self.result is not None and self.result.retcode != 0
