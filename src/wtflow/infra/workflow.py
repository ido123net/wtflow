from __future__ import annotations

import itertools
from dataclasses import dataclass
from typing import Iterator

from wtflow.infra.nodes import Node


@dataclass
class Workflow:
    name: str
    root: Node

    @property
    def nodes(self) -> list[Node]:
        return self._get_nodes(self.root)

    @property
    def id(self) -> str:
        return str(self._id) if hasattr(self, "_id") else self.name

    def set_id(self, id: int) -> None:
        self._id = id

    def _get_nodes(self, node: Node) -> list[Node]:
        nodes = [node]
        for child in node.children:
            nodes.extend(self._get_nodes(child))
        return nodes

    def _init_node(self, node: Node, counter: Iterator[int]) -> None:
        node.lft = next(counter)
        for child in node.children:
            self._init_node(child, counter)
        node.rgt = next(counter)

    def __post_init__(self) -> None:
        counter = itertools.count(1)
        self._init_node(self.root, counter)
        for node in self.nodes:
            node.set_workflow(self)

    def print(self) -> None:
        print(f"Workflow: {self.name}")
        self.root.print()
