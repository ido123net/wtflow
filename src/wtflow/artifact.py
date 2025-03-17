from __future__ import annotations

import pathlib
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from wtflow.nodes import Node


class ArtifactType(Enum):
    TXT = "txt"
    JSON = "json"
    CSV = "csv"


@dataclass
class Artifact:
    name: str
    type: ArtifactType = ArtifactType.TXT
    file_path: pathlib.Path | None = None

    _node: Node | None = field(default=None, repr=False)

    @property
    def path(self) -> pathlib.Path:
        if self.file_path is None:  # pragma: no cover
            raise ValueError("Artifact path not set")
        return self.file_path

    @path.setter
    def path(self, value: pathlib.Path) -> None:
        self.file_path = value

    @property
    def data(self) -> bytes:
        with open(self.path, "rb") as f:
            return f.read()


def create_default_artifacts() -> list[Artifact]:
    return [
        Artifact(name="stdout"),
        Artifact(name="stderr"),
    ]
