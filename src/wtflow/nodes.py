from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from wtflow.artifact import Artifact, create_default_artifacts
from wtflow.executables import Executable
from wtflow.utils import create_uuid

if TYPE_CHECKING:
    from wtflow.workflow import Workflow

logger = logging.getLogger(__name__)


@dataclass
class Node:
    name: str
    executable: Executable | None = None
    retcode: int | None = None
    parallel: bool = False
    children: list[Node] = field(default_factory=list)
    artifacts: list[Artifact] = field(default_factory=list)

    _id: str = field(default_factory=create_uuid, repr=False)
    _workflow: Workflow | None = field(default=None, repr=False)
    _parent: Node | None = field(default=None, repr=False)

    def __post_init__(self) -> None:
        if "stdout" in self._artifact_dict or "stderr" in self._artifact_dict:
            raise ValueError("`stdout` and `stderr` are reserved artifact names")
        self.artifacts = self.artifacts + create_default_artifacts()
        if self.executable:
            self.executable.set_node(self)
        if self.children:
            for child in self.children:
                child._parent = self

    @property
    def parent(self) -> Node | None:
        return self._parent  # pragma: no cover

    @property
    def id(self) -> str:
        return self._id

    @property
    def _artifact_dict(self) -> dict[str, Artifact]:
        return {artifact.name: artifact for artifact in self.artifacts}

    @property
    def stdout_artifact(self) -> Artifact:
        return self._artifact_dict["stdout"]

    @property
    def stderr_artifact(self) -> Artifact:
        return self._artifact_dict["stderr"]

    @property
    def stdout(self) -> bytes:
        return self.stdout_artifact.data

    @property
    def stderr(self) -> bytes:
        return self.stderr_artifact.data

    def execute(self) -> None:
        if self.executable:
            self.retcode = self.executable.execute()
