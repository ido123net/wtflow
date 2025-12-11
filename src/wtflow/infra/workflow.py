from __future__ import annotations

import itertools
import sys
from dataclasses import dataclass, field
from typing import Any, Iterator

from wtflow.infra.nodes import Node

if sys.version_info >= (3, 11):  # pragma: >=3.11 cover
    from typing import Self
else:  # pragma: <3.11 cover
    from typing_extensions import Self


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

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> Self:
        return cls(d["name"], root=Node.from_dict(d["root"]))

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "root": self.root.to_dict(),
        }
