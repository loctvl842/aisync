from __future__ import annotations

import abc
from typing import Any, Callable, Dict, Iterator, Literal, Optional, Sequence, Tuple, TypeVar, Union, overload

from langchain_core.runnables import RunnableConfig
from langchain_core.runnables.base import RunnableLike
from langgraph.types import All, StreamMode

from aisync.signalers.base import BaseSignaler

GraphInput = TypeVar("GraphInput", bound=Union[Dict[str, Any], Any])
"""Type variable for the initial input to the graph"""

GraphOutput = TypeVar("GraphOutput", bound=Union[Dict[str, Any], Any])
"""Type variable for final graph output"""

StreamChunk = TypeVar("StreamChunk", bound=Union[Dict[str, Any], Any])
"""Type variable for streaming chunks of data"""

# Callback function types
ChainStartCallback = Callable[[GraphInput], GraphInput]
"""Callback type for preprocessing input data"""

ChunkGeneratedCallback = Callable[[StreamChunk], StreamChunk]
"""Callback type for processing each generated chunk"""

ChainEndCallback = Callable[[list[StreamChunk]], None]
"""Callback type for processing final output"""


BaseConditionalBranchAction = Tuple["ConditionalBranch", Callable[..., list[str]]]


class Graph(abc.ABC):
    """A directed graph representing a workflow of connected nodes.

    This abstract base class defines the interface for a computational graph where nodes
    represent processing steps connected by directed edges. The graph supports sequential,
    parallel, and conditional execution patterns.

    The graph can be constructed using the >> operator for sequential connections,
    & operator for parallel branches, and | operator for conditional branches.

    Example:
        >>> node1 = Node("process", process_fn)
        >>> node2 = Node("validate", validate_fn)
        >>> node3 = Node("format", format_fn)
        >>> graph = node1 >> (node2 & node3)  # Sequential into parallel execution

    Methods
    -------
    compile()
        Compiles the graph into an executable form.

    invoke(input, config=None, **kwargs)
        Executes the graph with a single input and returns the final output.

    stream(input, config=None, **kwargs)
        Executes the graph and yields intermediate outputs as they are produced.

    run(max_workers: int, max_retries: int)
        Executes the graph with specified parallel workers and retry limits.

    execute_node(node: Node)
        Executes a single node in the graph.

    to_mermaid(direction="TD")
        Generates a Mermaid diagram representation of the graph.

    Parameters
    ----------
    input : GraphInput
        The input data to be processed by the graph.
    config : Optional[RunnableConfig]
        Configuration for the graph execution.
    stream_mode : StreamMode
        Mode for streaming output ("values", "updates", or "debug").
    output_keys : Optional[Union[str, Sequence[str]]]
        Keys to include in the output.
    on_chain_start : Optional[ChainStartCallback]
        Callback function to preprocess input before execution.
    on_chunk_generated : Optional[ChunkGeneratedCallback]
        Callback function to process intermediate outputs.
    on_chain_end : Optional[ChainEndCallback]
        Callback function to process final output.
    interrupt_before : Optional[Union[All, Sequence[str]]]
        Nodes to interrupt before execution.
    interrupt_after : Optional[Union[All, Sequence[str]]]
        Nodes to interrupt after execution.
    debug : Optional[bool]
        Enable debug mode for detailed execution information.

    Notes
    -----
    - The graph must be compiled before execution.
    - Supports both synchronous (invoke) and streaming execution modes.
    - Provides hooks for input preprocessing and output post-processing.
    - Can visualize the graph structure using Mermaid diagram syntax.
    """

    signaler: BaseSignaler

    @abc.abstractmethod
    def compile(self): ...

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
    ) -> GraphOutput: ...

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
    ) -> Iterator[StreamChunk]: ...

    def run(self, *, max_workers: int, max_retries: int) -> None: ...

    def execute_node(self, node: Node): ...

    def to_mermaid(self, direction: Literal["TD", "LR", "BT", "RL"] = "TD") -> str: ...

    @overload
    def __rshift__(self, other: Node) -> Graph: ...

    @overload
    def __rshift__(self, other: Graph) -> Graph: ...

    @overload
    def __rshift__(self, other: Branch) -> Graph: ...

    @overload
    def __rshift__(self, other: BaseConditionalBranchAction) -> Graph: ...

    @abc.abstractmethod
    def __rshift__(self, other: Union[Node, Graph, Branch, BaseConditionalBranchAction]) -> Graph: ...

    def __getattr__(self, node_name: str) -> Graph: ...


class Node(abc.ABC):
    @property
    @abc.abstractmethod
    def action(self) -> RunnableLike: ...

    @overload
    def __rshift__(self, other: Node) -> Graph: ...

    @overload
    def __rshift__(self, other: Graph) -> Graph: ...

    @overload
    def __rshift__(self, other: Branch) -> Graph: ...

    @overload
    def __rshift__(self, other: BaseConditionalBranchAction) -> Graph: ...

    @abc.abstractmethod
    def __rshift__(self, other: Union[Node, Graph, Branch, BaseConditionalBranchAction]) -> Graph: ...

    @overload
    def __and__(self, other: Node) -> Branch: ...

    @overload
    def __and__(self, other: Branch) -> Branch: ...

    @abc.abstractmethod
    def __and__(self, other: Union[Node, Branch]) -> Branch: ...


class Branch(abc.ABC):
    @overload
    def __rshift__(self, other: Node) -> Graph: ...

    @overload
    def __rshift__(self, other: Graph) -> Graph: ...

    @abc.abstractmethod
    def __rshift__(self, other: Union[Node, Graph]) -> Graph: ...

    @overload
    def __and__(self, other: Node) -> Branch: ...

    @overload
    def __and__(self, other: Branch) -> Branch: ...

    @abc.abstractmethod
    def __and__(self, other: Union[Node, Branch]) -> Branch: ...


class ConditionalBranch(abc.ABC):
    @overload
    def __or__(self, other: Node) -> ConditionalBranch: ...

    @overload
    def __or__(self, other: ConditionalBranch) -> ConditionalBranch: ...

    @abc.abstractmethod
    def __or__(self, other: Union[Node, ConditionalBranch]) -> ConditionalBranch: ...
