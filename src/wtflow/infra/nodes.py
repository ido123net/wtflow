from __future__ import annotations

import logging
from typing import Annotated

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field

logger = logging.getLogger(__name__)


class Node(BaseModel):
    name: str
    command: str | None = None
    timeout: float | None = None
    parallel: bool = False
    children: Annotated[tuple[Node, ...], BeforeValidator(lambda x: tuple(x))] = Field(default_factory=tuple)

    model_config = ConfigDict(frozen=True)
