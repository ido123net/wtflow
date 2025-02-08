from __future__ import annotations

import logging
from typing import Any, Union
from uuid import uuid4

from pydantic import BaseModel, Field, model_validator

from wtflow.definitions import Outcome, Result
from wtflow.executables import Command, PyFunc
from wtflow.executors import NodeExecutor

logger = logging.getLogger(__name__)


class Node(BaseModel):
    node_id: str = Field(default_factory=lambda: str(uuid4().hex), exclude=True)
    name: str
    outcome: Outcome = Outcome.INITIAL
    cmd: str | None = None
    executable: Union[PyFunc, Command] | None = Field(None, discriminator="type")
    stop_on_failure: bool = True
    timeout: int | None = None
    result: Result | None = None
    parallel: bool = False
    children: list[Node] = []
    _parent: Node | None = None

    def model_post_init(self, __context: Any) -> None:
        if self.children:
            for child in self.children:
                child._parent = self
        return super().model_post_init(__context)

    @model_validator(mode="before")
    @classmethod
    def validate_cmd_or_executable(cls, data: Any) -> Any:
        if data.get("cmd") and data.get("executable"):
            raise ValueError("`cmd` and `executable` are mutually exclusive")
        return data

    @property
    def parent(self) -> Node | None:
        return self._parent  # pragma: no cover

    async def execute(self) -> None:
        await NodeExecutor(self).execute()
