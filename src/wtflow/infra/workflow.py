from __future__ import annotations

import itertools
import logging
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel

from wtflow.infra.nodes import Node

if TYPE_CHECKING:
    from wtflow.infra.nodes import Node

logger = logging.getLogger(__name__)


class Workflow(BaseModel):
    name: str
    root: Node

    _id: int | None = None

    @property
    def id(self) -> int | str:
        return self._id if self._id else self.name

    @id.setter
    def id(self, value: int) -> None:
        self._id = value

    def model_post_init(self, context: Any, /) -> None:
        counter = itertools.count(1)
        self.root.set_lft_rgt(counter)
