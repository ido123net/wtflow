from __future__ import annotations

import logging
import sys
from dataclasses import dataclass, field
from typing import Any

from wtflow.infra.artifact import Artifact
from wtflow.infra.executables import Command, Executable
from wtflow.infra.executors import Result

if sys.version_info >= (3, 11):  # pragma: >=3.11 cover
    from typing import Self
else:  # pragma: <3.11 cover
    from typing_extensions import Self

logger = logging.getLogger(__name__)


@dataclass
class Node:
    name: str
    executable: Executable | None = None
    parallel: bool = False
    children: list[Node] = field(default_factory=list)
    artifacts: list[Artifact] = field(default_factory=list)

    result: Result | None = field(default=None, init=False)

    _stdout: Artifact = field(default_factory=lambda: Artifact(name="stdout"), repr=False, init=False)
    _stderr: Artifact = field(default_factory=lambda: Artifact(name="stderr"), repr=False, init=False)
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

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> Self:
        _executable = d.get("executable")
        executable = Command.from_dict(_executable) if _executable else None
        return cls(
            name=d["name"],
            executable=executable,
            parallel=d.get("parallel", False),
            children=[cls.from_dict(child) for child in d.get("children", [])],
            artifacts=[Artifact(**artifact) for artifact in d.get("artifacts", [])],
        )

    def to_dict(self) -> dict[str, Any]:
        res: dict[str, Any] = {"name": self.name}
        if self.executable:
            res["executable"] = self.executable.to_dict()
        if self.children:
            res["children"] = [child.to_dict() for child in self.children]
        if self.artifacts:
            res["artifacts"] = [artifact.to_dict() for artifact in self.artifacts]
        return res
