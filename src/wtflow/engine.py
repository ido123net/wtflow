import asyncio
import logging

from wtflow.workflow import Workflow

logger = logging.getLogger(__name__)


class Engine:
    def __init__(self, workflow: Workflow):
        self.workflow = workflow

    async def run(self) -> int:
        task = asyncio.create_task(self.workflow.root.execute())
        try:
            await task
            return 0
        except asyncio.CancelledError:
            return 1
        finally:
            logger.debug(f"workflow:\n{self.workflow.model_dump_json(indent=2)}")
