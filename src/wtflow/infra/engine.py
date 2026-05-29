from __future__ import annotations

import asyncio
import logging
from typing import Iterable

from wtflow.config import Config
from wtflow.infra.executors import NodeExecutor, NodeResult
from wtflow.infra.nodes import Node
from wtflow.infra.workflow import Workflow
from wtflow.services.servicer import Servicer

logger = logging.getLogger(__name__)


class Engine:
    def __init__(self, config: Config | None = None) -> None:
        self.config = config or Config()
        self.servicer = Servicer.from_config(self.config)

    async def run_workflow(self, workflow: Workflow) -> int:
        await self.servicer.db_service.add_workflow(workflow)
        result = await self.execute_workflow(workflow)
        await self.servicer.db_service.end_workflow(workflow, result)
        return result

    async def execute_workflow(self, workflow: Workflow) -> NodeResult:
        return await self.execute_node(workflow, workflow.root)

    async def execute_node(self, workflow: Workflow, node: Node) -> NodeResult:
        executor = NodeExecutor(workflow, node, self.servicer.storage_service)
        logger.debug(f"Start execution of {node.name!r}")
        await self.servicer.db_service.start_execution(workflow, node)
        result = await executor.execute_command(node.command) or await self.execute_children(workflow, node.children)
        logger.debug(f"End execution of {node.name!r}")
        logger.debug(f"Node {node.name!r} {result = }")
        await self.servicer.db_service.end_execution(workflow, node, result)
        return result

    async def execute_children(self, workflow: Workflow, children: Iterable[Node]) -> NodeResult:
        if not children:
            return NodeResult.SUCCESS

        tasks = [asyncio.create_task(self.execute_node(workflow, child)) for child in children]
        for result in asyncio.as_completed(tasks):
            if await result:
                _cancel_tasks(tasks)
                return NodeResult.CHILD_FAILED
        return NodeResult.SUCCESS


def _cancel_tasks(tasks: list[asyncio.Task[NodeResult]]) -> None:
    for task in tasks:
        task.cancel()
