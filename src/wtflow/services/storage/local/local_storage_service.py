import pathlib
from contextlib import contextmanager
from io import BufferedWriter
from typing import Generator

import wtflow
from wtflow.services.storage.storage_service import ArtifactWriter, StorageServiceInterface


class LocalArtifactWriter(ArtifactWriter):
    def __init__(self, path: pathlib.Path) -> None:
        self.path = path
        self._handle: BufferedWriter | None = None

    def write(self, data: bytes) -> int:
        if self._handle is None:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self._handle = self.path.open("ab")
        return self._handle.write(data)

    def close(self) -> None:
        if self._handle is not None:
            self._handle.close()
            self._handle = None


class LocalStorageService(StorageServiceInterface):
    def __init__(self, base_path: pathlib.Path | str) -> None:
        super().__init__()
        self.base_path = pathlib.Path(base_path)

    def _get_path(
        self,
        workflow: wtflow.Workflow,
        node: wtflow.Node,
        name: str,
        file_type: str,
    ) -> pathlib.Path:
        workflow_id = workflow.name
        node_id = node.name
        return self.base_path / str(workflow_id) / str(node_id) / f"{name}.{file_type}"

    @contextmanager
    def open_artifact(
        self,
        workflow: wtflow.Workflow,
        node: wtflow.Node,
        name: str,
        file_type: str = "txt",
    ) -> Generator[LocalArtifactWriter, None, None]:
        path = self._get_path(workflow, node, name, file_type)
        writer = LocalArtifactWriter(path)
        try:
            yield writer
        finally:
            writer.close()
