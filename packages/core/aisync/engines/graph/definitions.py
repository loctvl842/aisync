from __future__ import annotations

import uuid
from collections import deque
from concurrent.futures import Future, ThreadPoolExecutor, as_completed
from datetime import datetime
from functools import wraps
from typing import (
    Annotated,
    Any,
    Callable,
    Iterator,
    Literal,
    Optional,
    Sequence,
    Tuple,
    TypedDict,
    Union,
    get_type_hints,
    overload,
)

from langchain_core.runnables import RunnableConfig
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph
from langgraph.types import All, StreamMode

import aisync.utils as ut
from aisync.engines.graph.base import (
    Branch,
    ChainEndCallback,
    ChunkGeneratedCallback,
    ConditionalBranch,
    Graph,
    GraphOutput,
    Node,
    ChainStartCallback,
    GraphInput,
    StreamChunk,
)
from aisync.log import LogEngine
from aisync.signalers import Channel, InMemorySignaler, Signal


def add_messages(messages: list[tuple[str, str]], new_messages: list[tuple[str, str]]) -> list[tuple[str, str]]:
    """Function to add a new message to the messages list."""
    return messages + new_messages


class State(TypedDict):
    messages: Annotated[list[tuple[str, str]], add_messages]


_classes: Tuple[Graph, Node] = None


def _create_graph_classes() -> Tuple[Graph, Node]:
    global _classes
    if _classes:
        return _classes

    signaler = InMemorySignaler()

    ConditionalBranchAction = Tuple["_ConditionalBranch", Callable[..., list[str]]]

    class _Graph(Graph):
        def __init__(self, *nodes: Node):
            self.log = LogEngine(self.__class__.__name__)
            if not nodes:
                nodes = []
            self.nodes: dict[str, Node] = {}
            for node in nodes:
                self.nodes = ut.dict_deep_extend(self.nodes, node.all())

            self._app: CompiledStateGraph = None
            self.signaler = signaler

        def get_source(self) -> list[Node]:
            """
            Identify source nodes (nodes with no incoming edges)

            Returns:
                A list of source Node instances
            """
            all_nodes = set(self.nodes.values())
            nodes_with_incoming_edges = set()

            for node in self.nodes.values():
                for edge in node.edges:
                    if isinstance(edge, _Node):
                        nodes_with_incoming_edges.add(edge)
                    elif isinstance(edge, tuple):
                        branch, _ = edge
                        for node in branch.nodes.values():
                            nodes_with_incoming_edges.add(node)

            source_nodes = all_nodes - nodes_with_incoming_edges
            return list(source_nodes)

        def get_sink(self) -> list[Node]:
            """
            Identify sink nodes (nodes with no outgoing edges)

            Returns:
                A list of sink Node instances
            """
            sink_nodes = [node for node in self.nodes.values() if not node.edges]
            return sink_nodes

        def compile(self):
            langgraph_builder = StateGraph(State)
            sources = self.get_source()

            queue = deque(sources)
            compiled = set()
            for node in sources:
                langgraph_builder.add_node(node.alias, node.action, metadata={})
                compiled.add(node.name)
                langgraph_builder.add_edge(START, node.alias)

            while queue:
                current_node = queue.popleft()
                for edge in current_node.edges:
                    if isinstance(edge, _Node) and edge.name not in compiled:
                        langgraph_builder.add_node(edge.alias, edge.action, metadata={})
                        compiled.add(edge.name)
                        langgraph_builder.add_edge(current_node.alias, edge.alias)
                        queue.append(edge)
                    elif isinstance(edge, tuple):
                        cond_branch, cond_fn = edge
                        path_map = {}
                        for node in cond_branch.nodes.values():
                            if node.name not in compiled:
                                langgraph_builder.add_node(node.alias, node.action, metadata={})
                                compiled.add(node)
                                queue.append(node)
                            path_map[node.name] = node.name
                        langgraph_builder.add_conditional_edges(current_node.name, cond_fn, path_map)

            sink_nodes = self.get_sink()
            for node in sink_nodes:
                langgraph_builder.add_edge(node.alias, END)
            self._app = langgraph_builder.compile(debug=False)

        def invoke(
            self,
            input: GraphInput,
            config: Optional[RunnableConfig] = None,
            *,
            stream_mode: StreamMode = "values",
            output_keys: Optional[Union[str, Sequence[str]]] = None,
            on_chain_start: Optional[ChainStartCallback] = None,
            on_chunk_generated: Optional[ChunkGeneratedCallback] = None,
            on_chain_end: Optional[ChainEndCallback] = None,
            interrupt_before: Optional[Union[All, Sequence[str]]] = None,
            interrupt_after: Optional[Union[All, Sequence[str]]] = None,
            debug: Optional[bool] = None,
            **kwargs: Any,
        ) -> GraphOutput:
            """Run the graph with a single input and config.

            Args:
                input: The input data for the graph. It can be a dictionary or any other type.
                config: Optional. The configuration for the graph run.
                stream_mode: Optional[str]. The stream mode for the graph run. Default is "values".
                output_keys: Optional. The output keys to retrieve from the graph run.
                on_chain_start: Optional. A function to format the input before the graph run.
                on_chunk_generated: Optional. A function to format the output after each step.
                on_chain_end: Optional. A function to run on the output after the graph run.
                interrupt_before: Optional. The nodes to interrupt the graph run before.
                interrupt_after: Optional. The nodes to interrupt the graph run after.
                debug: Optional. Enable debug mode for the graph run.
                **kwargs: Additional keyword arguments to pass to the graph run.

            Returns:
                The output of the graph run. If stream_mode is "values", it returns the latest output.
                If stream_mode is not "values", it returns a list of output chunks.
            """
            if on_chain_start:
                try:
                    input = on_chain_start(input)
                except Exception as e:
                    self.log.error(f"Error in on_chain_start callback: {e}")
                    raise RuntimeError(f"Error in on_chain_start callback: {e}") from e
            output: ChainStartCallback = self._app.invoke(
                input,
                config,
                stream_mode=stream_mode,
                output_keys=output_keys,
                debug=debug,
                **kwargs,
            )
            if on_chunk_generated:
                try:
                    output = on_chunk_generated(output) if on_chunk_generated else output
                except Exception as e:
                    self.log.error(f"Error in on_chunk_generated callback: {e}")
                    raise RuntimeError(f"Error in on_chunk_generated callback: {e}") from e

            if on_chain_end:
                try:
                    on_chain_end(output)
                except Exception as e:
                    self.log.error(f"Error in on_chain_end callback: {e}")
                    raise RuntimeError(f"Error in on_chain_end callback: {e}") from e
            return output

        def stream(
            self,
            input: Union[dict[str, Any], Any],
            config: Optional[RunnableConfig] = None,
            *,
            stream_mode: Optional[Union[StreamMode, list[StreamMode]]] = None,
            output_keys: Optional[Union[str, Sequence[str]]] = None,
            on_chain_start: Optional[ChainStartCallback] = None,
            on_chunk_generated: Optional[ChunkGeneratedCallback] = None,
            on_chain_end: Optional[ChainEndCallback] = None,
            interrupt_before: Optional[Union[All, Sequence[str]]] = None,
            interrupt_after: Optional[Union[All, Sequence[str]]] = None,
            debug: Optional[bool] = None,
            subgraphs: bool = False,
        ) -> Iterator[StreamChunk]:
            """Stream graph steps for a single input.

            Args:
                input: The input to the graph.
                config: The configuration to use for the run.
                stream_mode: The mode to stream output, defaults to self.stream_mode.
                    Options are 'values', 'updates', and 'debug'.
                    values: Emit the current values of the state for each step.
                    updates: Emit only the updates to the state for each step.
                        Output is a dict with the node name as key and the updated values as value.
                    debug: Emit debug events for each step.
                output_keys: The keys to stream, defaults to all non-context channels.
                on_chain_start: Optional. A function to format the input before the graph run.
                on_chunk_generated: Optional. A function to format the output after each step.
                on_chain_end: Optional. A function to run on the output after the graph run.
                interrupt_before: Nodes to interrupt before, defaults to all nodes in the graph.
                interrupt_after: Nodes to interrupt after, defaults to all nodes in the graph.
                debug: Whether to print debug information during execution, defaults to False.
                subgraphs: Whether to stream subgraphs, defaults to False.

            Yields:
                The output of each step in the graph. The output shape depends on the stream_mode.
            """
            output: list[ChainStartCallback] = []
            if on_chain_start:
                try:
                    input = on_chain_start(input)
                except Exception as e:
                    self.log.error(f"Error in on_chain_start callback: {e}")
                    raise RuntimeError(f"Error in on_chain_start callback: {e}") from e

            for chunk in self._app.stream(
                input,
                config,
                stream_mode="messages",
                output_keys=output_keys,
                interrupt_before=interrupt_before,
                interrupt_after=interrupt_after,
                debug=debug,
                subgraphs=subgraphs,
            ):
                if on_chunk_generated:
                    try:
                        chunk = on_chunk_generated(chunk) if on_chunk_generated else chunk
                    except Exception as e:
                        self.log.error(f"Error in on_chunk_generated callback: {e}")
                        raise RuntimeError(f"Error in on_chunk_generated callback: {e}") from e
                if chunk:
                    output.append(chunk)
                    yield chunk

            if on_chain_end:
                try:
                    on_chain_end(output)
                except Exception as e:
                    self.log.error(f"Error in on_chain_end callback: {e}")
                    raise RuntimeError(f"Error in on_chain_end callback: {e}") from e

        def run(self, *, max_workers: int = None, max_retries: int = 3):
            """
            Execute the graph by traversing its nodes and executing their actions
            """
            sources = self.get_source()
            if not sources:
                self.log.warning("No source nodes found. Cannot run the graph")
                return

            queue = deque(sources)
            retries = {}

            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_to_node: dict[Future, Node] = {}

                while queue or future_to_node:
                    while queue:
                        current_node = queue.popleft()
                        if retries.get(current_node.name, 0) > max_retries:
                            self.log.warning(
                                f"Node {current_node.name} has reached the maximum retry limit ({max_retries}). Skipping execution."
                            )
                            continue
                        future = executor.submit(self.execute_node, current_node)
                        future_to_node[future] = current_node
                        retries[current_node.name] = (
                            0 if current_node.name not in retries else retries[current_node.name] + 1
                        )

                    done = as_completed(future_to_node)
                    for future in done:
                        current_node = future_to_node.pop(future)
                        try:
                            result = future.result()
                            self.log.info(f"Node {current_node.name} returned {result}")
                        except Exception as e:
                            retries[current_node.name] += 1
                            self.log.error(f"Error running node {current_node.name}: {e}")
                            continue
                        for edge in current_node.edges:
                            if isinstance(edge, _Node):
                                queue.append(edge)
                            elif isinstance(edge, tuple):
                                cond_branch, cond_fn = edge
                                selected_node_names = cond_fn()
                                if not isinstance(selected_node_names, list):
                                    raise TypeError(
                                        f"Condition function '{cond_fn.__name__}' must return a list of node names."
                                    )
                                for name in selected_node_names:
                                    branch_node = cond_branch.nodes.get(name)
                                    if branch_node:
                                        queue.append(branch_node)
                                    else:
                                        raise ValueError(
                                            f"Node '{name}' not found in ConditionalBranch '{cond_branch}'."
                                        )
                            else:
                                raise TypeError(f"Unknown edge type: {edge}")
                self.log.info("Graph execution completed.")

        def execute_node(self, node: Node):
            print(f"Executing Node: {node.name}")
            return node.call()

        def to_mermaid(self, direction: Literal["TD", "LR", "BT", "RL"] = "TD") -> str:
            """
            Generate a Mermaid diagram representation of the graph.

            Args:
                direction: The direction of the graph layout. Common options:
                    - TD: Top to Down
                    - LR: Left to Right
                    - BT: Bottom to Top
                    - RL: Right to Left

            Returns:
                A string containing the Mermaid diagram syntax.
            """
            lines = [f"graph {direction}"]
            for node in self.nodes.values():
                if isinstance(node, _Node):
                    for edge in node.edges:
                        if isinstance(edge, tuple) and isinstance(edge[0], _ConditionalBranch):
                            # Conditional branch represented with -.-> and labeled
                            cond_branch, condition_fn = edge
                            for branch_node in cond_branch.nodes.values():
                                lines.append(
                                    f"    {node.name}[{node.alias}] -.->|{condition_fn.__name__}| {branch_node.name}[{branch_node.alias}]"
                                )
                        elif isinstance(edge, _Node):
                            # Regular edge represented with -->
                            lines.append(f"    {node.name}[{node.alias}] --> {edge.name}[{edge.alias}]")
            return "\n".join(lines)

        @overload
        def __rshift__(self, other: Node) -> "Graph": ...

        @overload
        def __rshift__(self, other: "Graph") -> "Graph": ...

        @overload
        def __rshift__(self, other: _Branch) -> "Graph": ...

        @overload
        def __rshift__(self, other: ConditionalBranchAction) -> "Graph": ...

        def __rshift__(self, other: Union[Node, Graph, _Branch, ConditionalBranchAction]) -> Graph:
            if isinstance(other, _Node):
                # Graph >> Node
                sink_nodes = self.get_sink()
                for node in sink_nodes:
                    node.edges.append(other)
                return _Graph(*self.nodes.values(), other)
            elif isinstance(other, _Graph):
                # Graph >> Graph
                self_sink_nodes = self.get_sink()
                other_source_nodes = other.get_source()

                if len(self_sink_nodes) > 1 and len(other_source_nodes) > 1:
                    raise ValueError("Many-to-many connections are not allowed. Please connect manually.")

                for sink_node in self_sink_nodes:
                    for source_node in other_source_nodes:
                        sink_node.edges.append(source_node)

                return _Graph(*self.nodes.values(), *other.nodes.values())
            elif isinstance(other, _Branch):
                # Graph >> Branch
                self_sink_nodes = self.get_sink()
                for node in self_sink_nodes:
                    node >> other  # Node >> Branch
                return _Graph(*self.nodes.values(), *other.nodes.values())
            elif isinstance(other, tuple):
                # Graph >> (ConditionalBranch, condition_func)
                self_sink_nodes = self.get_sink()
                for node in self_sink_nodes:
                    node >> other
                return _Graph(*self.nodes.values(), *other[0].nodes.values())
            else:
                raise ValueError("Invalid right shift operator")

        def __getattr__(self, node_name: str):
            if node_name in self.nodes:
                return _SubGraph(self.nodes[node_name], self)
            raise AttributeError(f"'Graph' object has no attribute '{node_name}'")

        def __repr__(self):
            repr_str = "Graph:\n"
            for node in self.nodes.values():
                if isinstance(node, _Node):
                    connections = []
                    for edge in node.edges:
                        if isinstance(edge, tuple) and isinstance(edge[0], _ConditionalBranch):
                            cond_branch, condition_fn = edge
                            branch_repr = f"({', '.join(cond_branch.nodes.keys())}, {condition_fn.__name__})"
                            connections.append(branch_repr)
                        elif isinstance(edge, _Node):
                            connections.append(edge.name)
                    connections_str = ", ".join(connections) if connections else "None"
                    repr_str += f"  {node.name} -> [{connections_str}]\n"
                elif isinstance(node, _ConditionalBranch):
                    repr_str += f"  {repr(node)}\n"
            return repr_str.strip()

    class _SubGraph(_Graph):
        def __init__(self, node: Node, graph: Graph):
            self.starter = node
            self.parent = graph
            super().__init__(*node.all().values())

        def __rshift__(self, other: Union[Node, Graph]):
            if isinstance(other, _Node):
                self.parent.nodes = ut.dict_deep_extend(self.parent.nodes, other.all())
            elif isinstance(other, _Graph):
                self.parent.nodes = ut.dict_deep_extend(self.parent.nodes, other.nodes)
            else:
                raise ValueError("Right operand must be a Node or Graph")
            return self.starter >> other

    class _Branch(Branch):
        def __init__(self, *nodes: Node):
            if not nodes:
                nodes = []
            self.nodes: dict[str, Node] = {node.name: node for node in nodes}

        @overload
        def __rshift__(self, other: Node) -> Graph: ...

        @overload
        def __rshift__(self, other: Graph) -> Graph: ...

        def __rshift__(self, other: Union[Node, Graph]) -> Graph:
            if isinstance(other, _Node):
                # Branch >> Node
                for node in self.nodes.values():
                    node >> other  # Node >> Node
                return _Graph(*self.nodes.values(), other)
            elif isinstance(other, _Graph):
                # Branch >> Graph
                other_source_nodes = other.get_source()
                if len(self.nodes.values()) > 1 and len(other_source_nodes) > 1:
                    raise ValueError("Many-to-many connections are not allowed. Please connect manually.")

                for node in other_source_nodes:
                    self >> node  # Branch >> Node
                return _Graph(*self.nodes.values(), *other.nodes.values())
            else:
                raise ValueError("Invalid right shift operator")

        def __and__(self, other: Union[Node, _Branch]) -> _Branch:
            if isinstance(other, _Node):
                # Branch & Node
                return _Branch(*self.nodes.values(), other)
            elif isinstance(other, _Branch):
                # Branch & Branch
                return _Branch(*self.nodes.values(), *other.nodes.values())
            else:
                raise ValueError("Invalid and operator")

        def __repr__(self) -> str:
            return f"Branch({', '.join(self.nodes.keys())})"

    class _ConditionalBranch(ConditionalBranch):
        def __init__(self, *nodes: Node):
            if not nodes:
                nodes = []
            self.nodes: dict[str, Node] = {node.name: node for node in nodes}

        def __or__(self, other: Union[Node, _ConditionalBranch]) -> _ConditionalBranch:
            if isinstance(other, _Node):
                # ConditionalBranch | Node
                return _ConditionalBranch(*self.nodes.values(), other)
            elif isinstance(other, _ConditionalBranch):
                # ConditionalBranch | ConditionalBranch
                return _ConditionalBranch(*self.nodes.values(), *other.nodes.values())
            else:
                raise ValueError("Invalid or operator")

    class _Node(Node):
        def __init__(self, name: str, call_fn: Callable, llm: Optional[Any] = None):
            self.name = call_fn.__name__
            self.alias = name
            self.signaler = signaler
            self.llm = llm
            self.call = call_fn
            self.edges: list[Union[Node, ConditionalBranchAction]] = []

        @property
        def action(self):
            """Wraps `self.call`, injects `llm` if available, and modifies type hints to exclude `llm`."""
            original_type_hints = get_type_hints(self.call)
            adjusted_type_hints = {k: v for k, v in original_type_hints.items() if k != "llm"}

            @wraps(self.call)
            def action(*args, **kwargs):
                self.signaler.publish(
                    channel=Channel.NODE_EXECUTION,
                    message=Signal(
                        id=f"{uuid.uuid4()}",
                        channel=Channel.NODE_EXECUTION,
                        content="Beginning Node Execution",
                        timestamp=datetime.now(),
                    ),
                )
                if self.llm is not None:
                    kwargs["llm"] = self.llm
                return self.call(*args, **kwargs)

            action.__annotations__ = adjusted_type_hints
            return action

        def all(self, visited: Optional[set[str]] = None) -> dict[str, Node]:
            """
            Recursively gather all connected nodes, avoiding infinite recursion in cyclic graphs.

            Args:
                visited: A set of node names that have already been visited.

            Returns:
                A dictionary of all nodes reachable from this node.
            """
            if visited is None:
                visited = set()

            if self.name in visited:
                return {}

            visited.add(self.name)
            nodes = {self.name: self}

            for edge in self.edges:
                if isinstance(edge, _Node):
                    nodes = ut.dict_deep_extend(nodes, edge.all(visited))
                elif isinstance(edge, tuple):
                    branch, _ = edge
                    for node in branch.nodes.values():
                        nodes = ut.dict_deep_extend(nodes, node.all(visited))

            return nodes

        @overload
        def __rshift__(self, other: Node) -> Graph: ...

        @overload
        def __rshift__(self, other: Graph) -> Graph: ...

        @overload
        def __rshift__(self, other: _Branch) -> Graph: ...

        @overload
        def __rshift__(self, other: ConditionalBranchAction) -> Graph: ...

        def __rshift__(self, other: Union[Node, Graph, _Branch, ConditionalBranchAction]) -> Graph:
            if isinstance(other, _Node):
                # Node >> Node
                self.edges.append(other)
                return _Graph(self, other)
            elif isinstance(other, _Graph):
                # Node >> Graph
                source_nodes = other.get_source()
                self.edges.extend(source_nodes)
                return _Graph(self, *other.nodes.values())
            elif isinstance(other, _Branch):
                # Node >> Branch
                self.edges = list(other.nodes.values())
                return _Graph(self, *other.nodes.values())
            elif isinstance(other, tuple):
                # Node >> (ConditionalBranch, condition_func)
                branch, condition_func = other
                self.edges.append(other)
                return _Graph(self, *branch.nodes.values())
            else:
                raise ValueError("Invalid right shift operator")

        @overload
        def __and__(self, other: Node) -> _Branch: ...

        @overload
        def __and__(self, other: _Branch) -> _Branch: ...

        def __and__(self, other: Union[Node, _Branch]) -> _Branch:
            if isinstance(other, _Node):
                # Node & Node
                return _Branch(self, other)
            elif isinstance(other, _Branch):
                # Node & Branch
                return _Branch(self, *other.nodes.values())
            else:
                raise ValueError("Invalid and operator")

        def __or__(self, other: Union[Node, _ConditionalBranch]) -> _ConditionalBranch:
            if isinstance(other, _Node):
                # Node | Node
                return _ConditionalBranch(self, other)
            elif isinstance(other, _ConditionalBranch):
                # Node | ConditionalBranch
                return _Branch(self, *other.nodes.values())
            else:
                raise ValueError("Invalid or operator")

        def __repr__(self):
            def format_edge(edge):
                if isinstance(edge, _Node):
                    return edge.name
                elif isinstance(edge, tuple):  # Conditional branch case
                    branch, _ = edge
                    return " | ".join(node.name for node in branch.nodes.values())
                return "Unknown"

            connections = ", ".join(format_edge(edge) for edge in self.edges) if self.edges else "None"
            return f"Node({self.name}) -> [{connections}]"

    _classes = _Graph, _Node

    return _classes


__Graph, __Node = _create_graph_classes()


class _Graph(__Graph, Graph): ...


class _Node(__Node, Node): ...
