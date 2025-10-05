import pathlib

import wtflow
from wtflow.storage.service import StorageServiceInterface


class LocalStorageService(StorageServiceInterface):
    def __init__(self, base_path: pathlib.Path | str) -> None:
        self.base_path = pathlib.Path(base_path)

    def get_artifact_uri(
        self,
        artifact: wtflow.Artifact,
        workflow: wtflow.Workflow,
        node: wtflow.Node,
    ) -> str | None:
        path = self._get_path(artifact, workflow, node)
        artifact.uri = path.absolute().as_uri()
        return artifact.uri

    def _get_path(
        self,
        artifact: wtflow.Artifact,
        workflow: wtflow.Workflow,
        node: wtflow.Node,
    ) -> pathlib.Path:
        return self.base_path / workflow.id / node.id / f"{artifact.name}.txt"

    def append_to_artifact(
        self,
        artifact: wtflow.Artifact,
        workflow: wtflow.Workflow,
        node: wtflow.Node,
        data: bytes,
    ) -> None:
        artifact_path = self._get_path(artifact, workflow, node)
        artifact_path.parent.mkdir(parents=True, exist_ok=True)
        with artifact_path.open("ab") as f:
            f.write(data)
