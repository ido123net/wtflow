from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Iterator

from wtflow.infra.executables import Command

logger = logging.getLogger(__name__)


@dataclass
class Node:
    name: str
    executable: Command | None = None
    parallel: bool = False
    children: list[Node] = field(default_factory=list)

    _id: int | None = field(default=None, repr=False, init=False)
    _lft: int | None = field(default=None, repr=False, init=False)
    _rgt: int | None = field(default=None, repr=False, init=False)

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
