from __future__ import annotations

import itertools
from dataclasses import dataclass, field
from typing import Iterator

from wtflow.infra.nodes import Node


@dataclass
class Workflow:
    name: str
    root: Node

    _id: int | None = field(default=None, repr=False, init=False)

    @property
    def nodes(self) -> list[Node]:
        return self._get_nodes(self.root)

    @property
    def id(self) -> str:
        _id = self._id or self.name
        return str(_id)

    def _get_nodes(self, node: Node) -> list[Node]:
        nodes = [node]
        for child in node.children:
            nodes.extend(self._get_nodes(child))
        return nodes

    def _init_node(self, node: Node, counter: Iterator[int]) -> None:
        node._lft = next(counter)
        for child in node.children:
            self._init_node(child, counter)
        node._rgt = next(counter)

    def __post_init__(self) -> None:
        counter = itertools.count(1)
        self._init_node(self.root, counter)
