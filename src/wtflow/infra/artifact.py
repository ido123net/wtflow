from __future__ import annotations

import pathlib
import sys
from dataclasses import dataclass, field
from enum import Enum

DEFAULT_STREAMS = ("stdout", "stderr")


class ArtifactType(str, Enum):
    TXT = "txt"
    JSON = "json"
    CSV = "csv"


@dataclass
class Artifact:
    name: str
    type: ArtifactType = ArtifactType.TXT
    file_path: pathlib.Path | None = None

    _opened: bool = field(default=False, init=False, repr=False)
    _data: bytes = field(default=b"", init=False, repr=False)

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
        return self._data

    def write(self, data: bytes) -> None:
        self._data += data
        self._write_to_file(data)

    def _write_to_file(self, data: bytes) -> None:
        with self.path.open("ab") as f:
            f.write(data)


class StreamArtifact(Artifact):
    def _write_to_file(self, data: bytes) -> None:
        if self.file_path is None:
            getattr(sys, self.name).buffer.write(data)
        else:
            super()._write_to_file(data)


def create_default_artifacts() -> list[StreamArtifact]:
    return [StreamArtifact(name=stream) for stream in DEFAULT_STREAMS]
