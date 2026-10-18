from __future__ import annotations

import asyncio
import logging
import os
import signal
from enum import IntEnum
from graphlib import TopologicalSorter
from types import TracebackType
from typing import Self

from wtflow.config import Config
from wtflow.infra.artifact import Artifact
from wtflow.infra.info import ExecutionInfo, RunInfo
from wtflow.infra.nodes import Node
from wtflow.infra.workflow import Graph, Tree
from wtflow.services.db.db_service import DBService
from wtflow.services.storage.storage_service import StorageService

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
    except TimeoutError:
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
    storage_service: StorageService,
    workflow: Graph,
    node: Node,
    stream: asyncio.StreamReader,
    artifact: Artifact,
) -> None:
    with storage_service.open_artifact(workflow, node, artifact) as f:
        while data := await stream.readline():
            f.write(data)


class Executor:
    def __init__(self, graph: Graph, db_service: DBService, storage_service: StorageService) -> None:
        self.graph = graph
        self.db_service = db_service
        self.storage_service = storage_service
        self.run_info = RunInfo(graph=graph)
        self.ts = TopologicalSorter(self.graph)
        self._running = False
        self._running_tasks: set[asyncio.Task[tuple[Node, NodeResult]]] = set()

    def _start_ready_nodes(self) -> None:
        for ready_node in self.ts.get_ready():
            self._running_tasks.add(asyncio.create_task(self.execute_node(ready_node)))

    async def _is_done(self) -> bool:
        done_tasks = {task for task in self._running_tasks if task.done()}
        for done_task in done_tasks:
            node, result = await done_task
            self.ts.done(node)
            if result:
                return True

        self._running_tasks = self._running_tasks - done_tasks

        return not (self.ts.is_active() or self._running_tasks)

    async def execute(self) -> ExitCode:
        self.ts.prepare()
        self._running = True

        await self.start()
        while True:
            if await self._is_done():
                break
            self._start_ready_nodes()
            await asyncio.sleep(0.001)

        await self.end()
        return ExitCode.SUCCESS if not self._running_tasks else ExitCode.FAIL

    async def execute_node(self, node: Node) -> tuple[Node, NodeResult]:
        execution_info = ExecutionInfo(run_info=self.run_info, node=node)
        execution_info.start()
        await self.db_service.start_execution(execution_info)
        result = await self._execute_node(node)
        execution_info.end()
        await self.db_service.finish_execution(execution_info)
        return node, result

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
        return asyncio.create_task(_read_stream(self.storage_service, self.graph, node, stream, artifact))

    async def start(self) -> None:
        self.run_info.start()
        await self.db_service.start_run(self.run_info)

    async def end(self) -> None:
        self.run_info.end()
        await self.db_service.finish_run(self.run_info)


class Engine:
    def __init__(self, config: Config | None = None) -> None:
        self.config = config or Config()

    async def run_workflow(self, workflow: Tree) -> int:
        graph = workflow.as_graph()
        await self.db_service.save_graph(graph)
        executor = Executor(graph, self.db_service, self.storage_service)
        result = await executor.execute()
        return result

    def start(self) -> None:
        self.db_service = self.config.database.create_db_service()
        self.storage_service = self.config.storage.create_storage_service()

    def close(self) -> None:
        self.db_service.close()
        self.storage_service.close()

    def __enter__(self) -> Self:
        self.start()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        self.close()
