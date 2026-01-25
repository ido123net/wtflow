from __future__ import annotations

import logging
from typing import Iterator

from pydantic import BaseModel

logger = logging.getLogger(__name__)


class Node(BaseModel):
    name: str
    command: str | None = None
    timeout: float | None = None
    parallel: bool = False
    children: list[Node] = []

    _id: int | None = None
    _lft: int | None = None
    _rgt: int | None = None

    @property
    def lft(self) -> int:
        assert self._lft is not None
        return self._lft

    @lft.setter
    def lft(self, value: int) -> None:
        self._lft = value

    @property
    def rgt(self) -> int:
        assert self._rgt is not None
        return self._rgt

    @rgt.setter
    def rgt(self, value: int) -> None:
        self._rgt = value

    @property
    def id(self) -> int | str:
        return self._id if self._id else self.name

    @id.setter
    def id(self, value: int) -> None:
        self._id = value

    def set_lft_rgt(self, counter: Iterator[int]) -> None:
        self.lft = next(counter)
        for child in self.children:
            child.set_lft_rgt(counter)
        self.rgt = next(counter)
