from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field

from wtflow.infra.nodes import Node


@dataclass
class Graph:
    nodes: set[Node] = field(default_factory=set)
    edges: set[tuple[Node, Node]] = field(default_factory=set)

    def items(self) -> set[tuple[Node, tuple[Node, ...]]]:
        predecessors = defaultdict[Node, set[Node]](set)
        for parent, child in self.edges:
            predecessors[child].add(parent)
        return {(node, tuple(predecessors[node])) for node in self.nodes}


@dataclass(frozen=True)
class Workflow:
    name: str
    root: Node

    def as_graph(workflow: Workflow) -> Graph:
        graph = Graph()

        def _add_node(node: Node, parent: Node | None = None) -> Graph:
            graph.nodes.add(node)
            if parent is not None:
                graph.edges.add((node, parent))
            for child in node.children:
                _add_node(child, node)
            return graph

        return _add_node(workflow.root)
