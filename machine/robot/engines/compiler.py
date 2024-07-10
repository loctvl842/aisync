from langgraph.graph import START, END, StateGraph, MessagesState
from langgraph.graph.graph import CompiledGraph
from langchain_core.pydantic_v1 import BaseModel, Field
from typing import Annotated, Sequence, TypedDict, Callable, Any, Union
from langgraph.graph import MessagesState
import functools
from .node_core import NodeCore

class State(TypedDict):
    input: str
    agent_output: str

class Compiler:
    def __init__(self):
        self.state_type = None  # Placeholder for state datatype
        self.compiled_graph = None # Not compiled yet
        self.state_graph = None # No graph setup yet
        self.node_core = NodeCore(name="node_core")
        
    def activate(self, assistant):
        self.set_state()
        self.state_graph = StateGraph(self.state_type)
        kwargs = {"cur_node": self.node_core}
        self.node_core.activate(assistant)
        self.add_node("node_core",  self.gen_wrapper(self.node_core.invoke, self.node_core))
        for node_name, node in assistant.suit.nodes.items():
            node.activate(assistant)
            kwargs = {"cur_node": node}
            self.add_node(node_name, self.gen_wrapper(node.invoke, node))
            if node_name != "intent_manager":
                self.add_edge(node_name, "node_core")
        self.set_end_point("node_core")

    def gen_wrapper(self, fn, node):
        @functools.wraps(fn)
        async def wrapper(state, **kwargs):
            kwargs["cur_node"] = node
            return await fn(state, **kwargs)
        return wrapper

    def set_state(self):
        """
        Decide the state datatype of all nodes in the Graph.
        """
        self.state_type = State

    def add_edge(self, src: str, dest: str):
        """
        Add a direct edge between two nodes.
        """
        self.state_graph.add_edge(src, dest)

    def add_conditional_edge(self, src: str, condition: Callable[[Any], bool]):
        """
        Add a conditional edge between two nodes.
        """
        self.state_graph.add_conditional_edges(src, condition)

    def set_start_point(self, key: str):
        """
        Set the start point of the graph.
        """
        self.state_graph.set_entry_point(key)

    def set_end_point(self, key: str):
        """
        Set the end point of the graph.
        """
        self.state_graph.set_finish_point(key)

    def compile(self):
        """
        Compile the current state graph into a compiled graph.
        """
        self.compiled_graph = self.state_graph.compile()

    def add_node(self, node_name, node):
        """
        Add a node to the graph.
        """
        self.state_graph.add_node(node_name, node)

    async def ainvoke(self, input):
        """
        Executes the compiled graph starting from the entry point.
        
        :param initial_input: The initial input or state required to start the graph execution.
        :return: The final state or output after executing the graph.
        """
        if self.compiled_graph is None:
            raise Exception("Graph is not compiled yet.")
        return await self.compiled_graph.ainvoke(input)