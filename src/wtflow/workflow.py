from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterator

from wtflow.nodes import Node


@dataclass
class Workflow:
    name: str
    root: Node

    _id: int | None = field(default=None, repr=False)

    @property
    def id(self) -> int:
        if self._id is None:
            raise ValueError("Workflow ID is not set")
        return self._id

    @id.setter
    def id(self, value: int) -> None:
        self._id = value

    @property
    def nodes(self) -> list[Node]:
        return self._get_nodes(self.root)

    def _get_nodes(self, node: Node) -> list[Node]:
        nodes = [node]
        for child in node.children:
            nodes.extend(self._get_nodes(child))
        return nodes

    def _init_node(self, node: Node, counter: Iterator[int]) -> None:
        node._workflow = self
        node._lft = next(counter)
        for child in node.children:
            self._init_node(child, counter)
        node._rgt = next(counter)

    def __post_init__(self) -> None:
        counter = iter(range(1, 2 * len(self.nodes) + 1))
        self._init_node(self.root, counter)
