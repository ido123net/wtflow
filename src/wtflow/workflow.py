from __future__ import annotations

from dataclasses import dataclass, field

from wtflow.nodes import Node
from wtflow.utils import create_uuid


@dataclass
class Workflow:
    root: Node
    name: str | None = None

    _id: str = field(default_factory=create_uuid, repr=False)

    @property
    def id(self) -> str:
        return self._id

    @property
    def nodes(self) -> list[Node]:
        return self._get_nodes(self.root)

    def _get_nodes(self, node: Node) -> list[Node]:
        nodes = [node]
        for child in node.children:
            nodes.extend(self._get_nodes(child))
        return nodes

    def _init_node(self, node: Node) -> None:
        node._workflow = self
        for child in node.children:
            self._init_node(child)

    def __post_init__(self) -> None:
        self._init_node(self.root)
