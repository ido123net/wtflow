import pathlib

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
    ) -> pathlib.Path:
        return self.base_path / workflow.id / node.id / f"{name}.txt"

    def append_to_artifact(
        self,
        workflow: wtflow.Workflow,
        node: wtflow.Node,
        name: str,
        data: bytes,
    ) -> None:
        artifact_path = self._get_path(workflow, node, name)
        artifact_path.parent.mkdir(parents=True, exist_ok=True)
        with artifact_path.open("ab") as f:
            f.write(data)
