from __future__ import annotations

import sys
from abc import ABC, abstractmethod

import wtflow


class StorageServiceInterface(ABC):
    @abstractmethod
    def append_to_artifact(
        self,
        workflow: wtflow.Workflow,
        node: wtflow.Node,
        name: str,
        data: bytes,
    ) -> None:
        raise NotImplementedError


class NoStorageService(StorageServiceInterface):
    def append_to_artifact(
        self,
        workflow: wtflow.Workflow,
        node: wtflow.Node,
        name: str,
        data: bytes,
    ) -> None:
        if name == "stdout":
            sys.stdout.buffer.write(data)
        elif name == "stderr":
            sys.stderr.buffer.write(data)
        else:
            raise NotImplementedError(f"Artifact {name} is not supported in {self.__class__.__name__}")
