from __future__ import annotations

import pathlib
from abc import ABC, abstractmethod
from typing import NamedTuple

import wtflow


class NodeLogs(NamedTuple):
    stdout: pathlib.Path | None = None
    stderr: pathlib.Path | None = None


class StorageServiceInterface(ABC):
    @abstractmethod
    def create_node_logs(self, workflow: wtflow.Workflow, node: wtflow.Node) -> NodeLogs: ...


class NoStorageService(StorageServiceInterface):
    def create_node_logs(self, workflow: wtflow.Workflow, node: wtflow.Node) -> NodeLogs:
        return NodeLogs()
