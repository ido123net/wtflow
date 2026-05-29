from __future__ import annotations

import asyncio
import logging
from enum import IntEnum
from graphlib import TopologicalSorter

from wtflow.config import Config
from wtflow.infra.executors import NodeExecutor, NodeResult
from wtflow.infra.nodes import Node
from wtflow.infra.workflow import Workflow
from wtflow.services.servicer import Servicer

logger = logging.getLogger(__name__)


class ExitCode(IntEnum):
    SUCCESS = 0
    FAIL = 1


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
        executor = NodeExecutor(workflow, node, self.servicer.storage_service)
        logger.debug(f"Start execution of {node.name!r}")
        await self.servicer.db_service.start_execution(workflow, node)
        result = await executor.execute_command(node.command)
        logger.debug(f"End execution of {node.name!r}")
        logger.debug(f"Node {node.name!r} {result = }")
        await self.servicer.db_service.end_execution(workflow, node, result)
        ts.done(node)
        return result


def _cancel_tasks(tasks: list[asyncio.Task[NodeResult]]) -> None:
    for task in tasks:
        task.cancel()
