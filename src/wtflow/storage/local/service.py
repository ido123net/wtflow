import pathlib

import wtflow
from wtflow.storage.service import NodeLogs, StorageServiceInterface


class LocalStorageService(StorageServiceInterface):
    def __init__(self, base_path: pathlib.Path | str) -> None:
        self.base_path = pathlib.Path(base_path)

    def create_node_logs(self, workflow: wtflow.Workflow, node: wtflow.Node) -> NodeLogs:
        return NodeLogs(
            stdout=self.base_path / workflow.id / node.id / "stdout.txt",
            stderr=self.base_path / workflow.id / node.id / "stderr.txt",
        )
