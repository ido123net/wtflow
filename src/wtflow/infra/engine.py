from __future__ import annotations

import asyncio
import logging
import os
import signal
from enum import IntEnum
from graphlib import TopologicalSorter

from wtflow.config import Config
from wtflow.infra.artifact import Artifact
from wtflow.infra.nodes import Node
from wtflow.infra.workflow import Workflow
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
    workflow: Workflow,
    node: Node,
    stream: asyncio.StreamReader,
    artifact: Artifact,
) -> None:
    with storage_service.open_artifact(workflow, node, artifact) as f:
        while data := await stream.readline():
            f.write(data)


class Engine:
    def __init__(self, config: Config | None = None) -> None:
        self.config = config or Config()
        self.servicer = Servicer.from_config(self.config)

    async def run_workflow(self, workflow: Workflow) -> int:
        await self.servicer.db_service.add_workflow(workflow)
        result = await self.execute_workflow(workflow)
        await self.servicer.db_service.end_workflow(workflow, result)
        return result

    async def execute_workflow(self, workflow: Workflow) -> ExitCode:
        graph = workflow.as_graph()
        ts = TopologicalSorter(graph)
        ts.prepare()
        while ts.is_active():
            ready_nodes = ts.get_ready()
            tasks = [asyncio.create_task(self.execute_node(workflow, node, ts)) for node in ready_nodes]
            for future_result in asyncio.as_completed(tasks):
                result = await future_result
                if result:
                    _cancel_tasks(tasks)
                    return ExitCode.FAIL
        return ExitCode.SUCCESS

    async def execute_node(self, workflow: Workflow, node: Node, ts: TopologicalSorter[Node]) -> NodeResult:
        if not node.command:
            ts.done(node)
            return NodeResult.SUCCESS

        logger.debug(f"Start execution of {node.name!r}")
        await self.servicer.db_service.start_execution(workflow, node)
        process = await _start_process(node.command)
        assert process.stdout and process.stderr
        stdout_task = asyncio.create_task(
            _read_stream(self.servicer.storage_service, workflow, node, process.stdout, node.stdout_artifact)
        )
        stderr_task = asyncio.create_task(
            _read_stream(self.servicer.storage_service, workflow, node, process.stderr, node.stderr_artifact)
        )
        result, *_ = await asyncio.gather(_wait_process(process, node.timeout), stdout_task, stderr_task)

        logger.debug(f"End execution of {node.name!r}")
        logger.debug(f"Node {node.name!r} {result = }")
        await self.servicer.db_service.end_execution(workflow, node, result)
        ts.done(node)
        return result


def _cancel_tasks(tasks: list[asyncio.Task[NodeResult]]) -> None:
    for task in tasks:
        task.cancel()
