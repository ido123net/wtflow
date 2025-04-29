from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from wtflow.artifact import Artifact, StreamArtifact, create_default_artifacts
from wtflow.executables import Executable

if TYPE_CHECKING:
    from wtflow.workflow import Workflow

logger = logging.getLogger(__name__)


@dataclass
class Node:
    name: str
    executable: Executable | None = None
    retcode: int | None = None
    stdout: bytes | None = None
    stderr: bytes | None = None
    parallel: bool = False
    children: list[Node] = field(default_factory=list)
    artifacts: list[Artifact] = field(default_factory=list)
    id: int | None = field(default=None, repr=False, init=False)
    _workflow: Workflow | None = field(default=None, repr=False, init=False)

    lft: int | None = field(default=None, repr=False)
    rgt: int | None = field(default=None, repr=False)

    def __post_init__(self) -> None:
        if "stdout" in self._artifact_dict or "stderr" in self._artifact_dict:
            raise ValueError("`stdout` and `stderr` are reserved artifact names")
        if self.executable:
            self.artifacts = [*self.artifacts, *create_default_artifacts()]
            self.executable.set_node(self)

    @property
    def _artifact_dict(self) -> dict[str, Artifact | StreamArtifact]:
        return {artifact.name: artifact for artifact in self.artifacts}

    @property
    def stdout_artifact(self) -> StreamArtifact:
        res = self._artifact_dict["stdout"]
        if TYPE_CHECKING:
            assert isinstance(res, StreamArtifact)
        return res

    @property
    def stderr_artifact(self) -> StreamArtifact:
        res = self._artifact_dict["stderr"]
        if TYPE_CHECKING:
            assert isinstance(res, StreamArtifact)
        return res

    def execute(self) -> None:
        if self.executable:
            self.retcode, self.stdout, self.stderr = self.executable.execute()

    def set_workflow(self, workflow: Workflow) -> None:
        self._workflow = workflow

    @property
    def stream_artifacts(self) -> tuple[StreamArtifact, StreamArtifact]:
        return self.stdout_artifact, self.stderr_artifact
