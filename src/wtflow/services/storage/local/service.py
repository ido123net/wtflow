import pathlib
from contextlib import contextmanager
from typing import Generator

import wtflow
from wtflow.services.storage.service import StorageServiceInterface


class LocalStorageService(StorageServiceInterface):
    def __init__(self, base_path: pathlib.Path | str) -> None:
        self.base_path = pathlib.Path(base_path)

    def _get_path(
        self,
        workflow: wtflow.Workflow,
        node: wtflow.Node,
        name: str,
        file_type: str,
    ) -> pathlib.Path:
        return self.base_path / str(workflow.id) / str(node.id) / f"{name}.{file_type}"

    @contextmanager
    def open_artifact(
        self,
        workflow: wtflow.Workflow,
        node: wtflow.Node,
        name: str,
        file_type: str = "txt",
    ) -> Generator[int, None, None]:
        artifact_path = self._get_path(workflow, node, name, file_type)
        artifact_path.parent.mkdir(parents=True, exist_ok=True)
        with artifact_path.open("ab") as f:
            yield f.fileno()
