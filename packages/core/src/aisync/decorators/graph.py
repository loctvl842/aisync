import re
from typing import Callable, Optional

from langgraph.graph import END, START


class Graph:
    def __init__(self, name: str, call_fn: Callable):
        self.name = name
        self.nodes = {}
        self.edges = []
        self.mermaid_code = call_fn()
        self.parse_mermaid_code()

    def parse_mermaid_code(self):
        lines = self.mermaid_code.strip().splitlines()

        edge_pattern = re.compile(r"(\w+)\s*-->\s*(\w+)")

        for line in lines[1:]:
            match = edge_pattern.match(line.strip())
            if match:
                start, end = match.groups()
                start = START if start == "START" else start
                end = END if end == "END" else end
                self.edges.append((start, end))
                self.nodes.setdefault(start, {}).update({"type": "node"})
                self.nodes.setdefault(end, {}).update({"type": "node"})


def graph(*args, name: Optional[str] = None):
    def _make_with_name(graph_name: str) -> Callable:
        def _make_graph(call_fn: Callable) -> Graph:
            node_ = Graph(graph_name, call_fn)
            return node_

        return _make_graph

    if len(args) == 1 and isinstance(args[0], str):
        # Then, called as @graph("name")
        return _make_with_name(args[0])
    elif len(args) == 1 and callable(args[0]):
        # Then, called as @graph
        func = args[0]
        graph_name = name if name else func.__name__
        return _make_with_name(graph_name)(func)
    elif len(args) == 0 and name:
        # Then, called as @graph(name="name")
        return _make_with_name(name)
    elif len(args) == 0:
        # Then, called as @graph(*args, **kwargs)
        def _decorator(call_fn):
            return _make_with_name(call_fn.__name__)(call_fn)

        return _decorator
    else:
        raise ValueError("Invalid usage of @graph")
