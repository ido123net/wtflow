from __future__ import annotations

import sys
from abc import ABC, abstractmethod
from contextlib import AbstractContextManager, contextmanager
from typing import BinaryIO, Generator

import wtflow
from wtflow.services.base_service import BaseService


class ArtifactWriter(ABC):
    @abstractmethod
    def write(self, data: bytes) -> int:
        raise NotImplementedError

    @abstractmethod
    def close(self) -> None:
        raise NotImplementedError


class StorageServiceInterface(BaseService):
    @abstractmethod
    def open_artifact(
        self,
        workflow: wtflow.Graph,
        node: wtflow.Node,
        artifact: wtflow.Artifact,
    ) -> AbstractContextManager[ArtifactWriter]:
        raise NotImplementedError


class StreamArtifactWriter(ArtifactWriter):
    def __init__(self, stream: BinaryIO) -> None:
        self.stream = stream

    def write(self, data: bytes) -> int:
        return self.stream.write(data)

    def close(self) -> None:
        pass


class NoStorageService(StorageServiceInterface):
    @contextmanager
    def open_artifact(
        self,
        workflow: wtflow.Graph,
        node: wtflow.Node,
        artifact: wtflow.Artifact,
    ) -> Generator[StreamArtifactWriter, None, None]:
        if artifact.name == "stdout":
            writer = StreamArtifactWriter(sys.stdout.buffer)
        elif artifact.name == "stderr":
            writer = StreamArtifactWriter(sys.stderr.buffer)
        else:
            raise NotImplementedError(f"Artifact {artifact.name} is not supported in {self.__class__.__name__}")
        try:
            yield writer
        finally:
            writer.close()
