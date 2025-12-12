from __future__ import annotations

import sys
from abc import ABC, abstractmethod

import wtflow


class StorageServiceInterface(ABC):
    @abstractmethod
    def append_to_artifact(
        self,
        artifact: wtflow.Artifact,
        workflow: wtflow.Workflow,
        node: wtflow.Node,
        data: bytes,
    ) -> None:
        raise NotImplementedError


class NoStorageService(StorageServiceInterface):
    def append_to_artifact(
        self,
        artifact: wtflow.Artifact,
        workflow: wtflow.Workflow,
        node: wtflow.Node,
        data: bytes,
    ) -> None:
        if artifact.name == "stdout":
            sys.stdout.buffer.write(data)
        elif artifact.name == "stderr":
            sys.stderr.buffer.write(data)
        else:
            raise NotImplementedError(f"Artifact {artifact.name} is not supported in {self.__class__.__name__}")
