from typing import (
    TYPE_CHECKING,
    Annotated,
    Any,
    Callable,
    Dict,
    Iterator,
    Optional,
    Sequence,
    TypedDict,
    TypeVar,
    Union,
)

from langchain_core.runnables import Runnable
from langchain_core.runnables.config import RunnableConfig
from langgraph.graph import StateGraph
from langgraph.graph.state import CompiledStateGraph
from langgraph.types import All, StreamMode

from aisync.log import log

if TYPE_CHECKING:
    from aisync.suit import Suit


def add_messages(messages: list[tuple[str, str]], new_messages: list[tuple[str, str]]) -> list[tuple[str, str]]:
    """Function to add a new message to the messages list."""
    return messages + new_messages


class State(TypedDict):
    messages: Annotated[list[tuple[str, str]], add_messages]


TInput = TypeVar("TInput", bound=Union[dict[str, Any], Any])
TModifiedInput = TypeVar("TModifiedInput", bound=Union[Dict[str, Any], Any])
TChunk = TypeVar("TChunk", bound=Union[Dict[str, Any], Any])
TOutput = TypeVar("TOutput", bound=Union[Dict[str, Any], Any])


class Workflow(Runnable[Union[dict[str, Any], Any], Union[dict[str, Any], Any]]):
    """
    A Workflow layer built on top of LangGraph's CompiledGraph, enabling configurable,
    step-based execution of tasks defined in a Suit object. Each workflow consists of
    interconnected nodes with specified actions and dependencies, supporting dynamic execution
    and output streaming.

    Args:
        suit (Suit): The Suit object containing nodes and graph structure for the workflow.

    Attributes:
        _app (Graph): The compiled graph of nodes and edges representing the workflow.
    """

    def __init__(self, suit: "Suit"):
        self._suit = suit
        self._app: CompiledStateGraph = None
        self.compile_graph()

    @property
    def suit(self):
        return self._suit

    @property
    def app(self):
        if not self._app:
            self.compile_graph()
        return self._app

    def compile_graph(self):
        graph_builder = StateGraph(State)
        graph = self.find_graph(self.suit)
        all_nodes = self.suit.nodes.values()
        for node in all_nodes:
            graph_builder.add_node(
                node.name,
                node.action,
                metadata={},
            )
        for edge in graph.edges:
            graph_builder.add_edge(*edge)
        self._app = graph_builder.compile(debug=False)

    def find_graph(self, suit: "Suit"):
        graphs = suit.graphs
        if len(graphs) == 0:
            raise ValueError("No graphs found in suit")
        # Default using latest version
        graph_name = max(graphs.keys())
        return graphs[graph_name]

    def invoke(
        self,
        input: TInput,
        config: Optional[RunnableConfig] = None,
        *,
        stream_mode: StreamMode = "values",
        output_keys: Optional[Union[str, Sequence[str]]] = None,
        on_chain_start: Optional[Callable[[TInput], TModifiedInput]] = None,
        on_chunk_generated: Optional[Callable[[TOutput], TChunk]] = None,
        on_chain_end: Optional[Callable[[TChunk], None]] = None,
        interrupt_before: Optional[Union[All, Sequence[str]]] = None,
        interrupt_after: Optional[Union[All, Sequence[str]]] = None,
        debug: Optional[bool] = None,
        **kwargs: Any,
    ) -> TChunk:
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
                log.error(f"Error in on_chain_start callback: {e}")
                raise RuntimeError(f"Error in on_chain_start callback: {e}") from e
        output: TChunk = self._app.invoke(
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
                log.error(f"Error in on_chunk_generated callback: {e}")
                raise RuntimeError(f"Error in on_chunk_generated callback: {e}") from e

        if on_chain_end:
            try:
                on_chain_end(output)
            except Exception as e:
                log.error(f"Error in on_chain_end callback: {e}")
                raise RuntimeError(f"Error in on_chain_end callback: {e}") from e
        return output

    def stream(
        self,
        input: Union[dict[str, Any], Any],
        config: Optional[RunnableConfig] = None,
        *,
        stream_mode: Optional[Union[StreamMode, list[StreamMode]]] = None,
        output_keys: Optional[Union[str, Sequence[str]]] = None,
        on_chain_start: Optional[Callable[[Union[dict[str, Any], Any]], None]] = None,
        on_chunk_generated: Optional[Callable[[dict[str, Any] | Any], dict[str, Any] | Any]] = None,
        on_chain_end: Optional[Callable[[dict[str, Any] | Any], dict[str, Any] | Any]] = None,
        interrupt_before: Optional[Union[All, Sequence[str]]] = None,
        interrupt_after: Optional[Union[All, Sequence[str]]] = None,
        debug: Optional[bool] = None,
        subgraphs: bool = False,
    ) -> Iterator[TChunk]:
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
        output: list[TChunk] = []
        if on_chain_start:
            try:
                input = on_chain_start(input)
            except Exception as e:
                log.error(f"Error in on_chain_start callback: {e}")
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
                    log.error(f"Error in on_chunk_generated callback: {e}")
                    raise RuntimeError(f"Error in on_chunk_generated callback: {e}") from e
            if chunk:
                output.append(chunk)
                yield chunk

        if on_chain_end:
            try:
                on_chain_end(output)
            except Exception as e:
                log.error(f"Error in on_chain_end callback: {e}")
                raise RuntimeError(f"Error in on_chain_end callback: {e}") from e
