from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict

from wtflow.infra.nodes import Node

if TYPE_CHECKING:
    from wtflow.infra.nodes import Node

logger = logging.getLogger(__name__)


class Workflow(BaseModel):
    name: str
    root: Node

    model_config = ConfigDict(frozen=True)
