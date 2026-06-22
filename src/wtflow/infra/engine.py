from __future__ import annotations

import asyncio
import logging
import os
import signal
from enum import IntEnum
from graphlib import TopologicalSorter

from wtflow.config import Config
from wtflow.infra.artifact import Artifact
from wtflow.infra.info import ExecutionInfo, RunInfo, execute
from wtflow.infra.nodes import Node
from wtflow.infra.workflow import Graph, Tree
from wtflow.services.servicer import Servicer
from wtflow.services.storage.storage_service import StorageServiceInterface

logger = logging.getLogger(__name__)


class ExitCode(IntEnum):
    SUCCESS = 0
    FAIL = 1


class NodeResult(IntEnum):
    SUCCESS = 0
    FAIL = 1
    TIMEOUT = 2
    CANCEL = 3


async def _wait_process(process: asyncio.subprocess.Process, timeout: float | None) -> NodeResult:
    try:
        result = await asyncio.wait_for(process.wait(), timeout)
        return NodeResult.FAIL if result else NodeResult.SUCCESS
    except asyncio.TimeoutError:
        return NodeResult.TIMEOUT
    except asyncio.CancelledError:
        return NodeResult.CANCEL
    finally:
        if process.returncode is None:
            os.killpg(os.getpgid(process.pid), signal.SIGTERM)
        await process.wait()


async def _start_process(command: str) -> asyncio.subprocess.Process:
    return await asyncio.create_subprocess_shell(
        command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        start_new_session=True,
    )


async def _read_stream(
    storage_service: StorageServiceInterface,
    workflow: Graph,
    node: Node,
    stream: asyncio.StreamReader,
    artifact: Artifact,
) -> None:
    with storage_service.open_artifact(workflow, node, artifact) as f:
        while data := await stream.readline():
            f.write(data)


class Executor:
    def __init__(self, graph: Graph, servicer: Servicer) -> None:
        self.graph = graph
        self.servicer = servicer

    async def execute(self) -> ExitCode:
        ts = TopologicalSorter(self.graph)
        ts.prepare()
        while ts.is_active():
            ready_nodes = ts.get_ready()
            tasks = [asyncio.create_task(self.execute_node(node, ts)) for node in ready_nodes]
            for future_result in asyncio.as_completed(tasks):
                result = await future_result
                if result:
                    _cancel_tasks(tasks)
                    return ExitCode.FAIL
        return ExitCode.SUCCESS

    async def execute_node(self, node: Node, ts: TopologicalSorter[Node]) -> NodeResult:
        execution_info = ExecutionInfo(self.graph, node)
        try:
            with execute(execution_info):
                await self.servicer.db_service.update_execution_info(execution_info)
                result = await self._execute_node(node)
            await self.servicer.db_service.update_execution_info(execution_info)
            return result
        finally:
            ts.done(node)

    async def _execute_node(self, node: Node) -> NodeResult:
        if not node.command:
            return NodeResult.SUCCESS

        process = await _start_process(node.command)
        stream_tasks = [self._stream_task(node, process, artifact_name) for artifact_name in ("stdout", "stderr")]
        result = await _wait_process(process, node.timeout)
        await asyncio.gather(*stream_tasks)
        return result

    def _stream_task(
        self,
        node: Node,
        process: asyncio.subprocess.Process,
        artifact_name: str,
    ) -> asyncio.Task[None]:
        artifact = Artifact(artifact_name)
        stream: asyncio.StreamReader = getattr(process, artifact_name)
        return asyncio.create_task(_read_stream(self.servicer.storage_service, self.graph, node, stream, artifact))


class Engine:
    def __init__(self, config: Config | None = None) -> None:
        self.config = config or Config()
        self.servicer = Servicer.from_config(self.config)

    async def run_workflow(self, workflow: Tree) -> int:
        graph = workflow.as_graph()
        await self.servicer.db_service.save_graph(graph)
        run_info = RunInfo(graph)
        with execute(run_info):
            await self.servicer.db_service.update_run_info(run_info)
            executor = Executor(graph, self.servicer)
            result = await executor.execute()
        await self.servicer.db_service.update_run_info(run_info)
        return result


def _cancel_tasks(tasks: list[asyncio.Task[NodeResult]]) -> None:
    for task in tasks:
        task.cancel()
