from __future__ import annotations

from abc import abstractmethod
from contextlib import AbstractContextManager, nullcontext

import wtflow
from wtflow.services.base_service import BaseService
from wtflow.services.db.db_service import DBServiceInterface, NoDBService


class StorageServiceInterface(BaseService):
    def __init__(self, db_service: DBServiceInterface | None = None) -> None:
        self.db_service = db_service or NoDBService()

    def start(self) -> None:
        pass

    def stop(self) -> None:
        pass

    @abstractmethod
    def open_artifact(
        self,
        workflow: wtflow.Workflow,
        node: wtflow.Node,
        name: str,
        file_type: str = "txt",
    ) -> AbstractContextManager[int | None]:
        raise NotImplementedError


class NoStorageService(StorageServiceInterface):
    def open_artifact(
        self,
        workflow: wtflow.Workflow,
        node: wtflow.Node,
        name: str,
        file_type: str = "txt",
    ) -> nullcontext[None]:
        if name in ("stdout", "stderr"):
            return nullcontext()
        else:
            raise NotImplementedError(f"Artifact {name} is not supported in {self.__class__.__name__}")
