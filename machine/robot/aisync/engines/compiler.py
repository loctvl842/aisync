import functools
from tracemalloc import start
from typing import TYPE_CHECKING, Any, Callable, Dict, TypedDict

from langchain_core.prompts import PromptTemplate
from langgraph.graph import StateGraph
from pydantic import BaseModel, Field

import core.utils as utils
from core.logger import syslog
from core.settings import settings

from .prompts import DEFAULT_CHOOSE_AGENT_PROMPT, DEFAULT_PROMPT_PREFIX

if TYPE_CHECKING:
    from ..assistants.base.assistant import Assistant
    from .node import Node


class AISyncInput(BaseModel):
    """
    Model for the input to the AISync engine.
    """

    query: str = Field("", description="Default field")


class State(TypedDict):
    input: AISyncInput
    agent_output: str


class Compiler:
    def __init__(self):
        self.state_type = None  # Placeholder for state datatype
        self.compiled_graph = None  # Not compiled yet
        self.state_graph = None  # No graph setup yet
        self.all_nodes = {}

    def setup_node_core(self, assistant: "Assistant") -> None:
        """
        Function to create a core node in the graph workflow
        """
        # This node has access to all documents available
        from .node_core import NodeCore

        docs = [doc.split("/")[-1] for doc in assistant.all_files_path]
        self.node_core = NodeCore(
            name="node_core",
            document_names=docs,
            prompt_prefix=assistant.suit.execute_hook(
                "build_prompt_prefix", default=DEFAULT_PROMPT_PREFIX, assistant=assistant
            ),
        )
        self.node_core.activate(assistant, True)
        self.add_node(self.node_core)

    def activate(self, assistant: "Assistant") -> None:
        self.set_state()
        self.state_graph = StateGraph(self.state_type)
        self.setup_node_core(assistant)
        should_customize_node_llm = assistant.suit.execute_hook("should_customize_node_llm")
        for node_name, node in assistant.suit.nodes.items():
            node.activate(assistant, should_customize_node_llm)
            self.add_node(node)
            self.add_conditional_edge(node_name, self.wrapper_choose_agent(node, assistant))
        if len(assistant.suit.nodes) == 0:
            self.set_start_point("node_core")
        self.set_end_point("node_core")

    def gen_wrapper(self, fn: callable, node: "Node") -> Callable:
        @functools.wraps(fn)
        async def wrapper(state, **kwargs):
            kwargs["cur_node"] = node
            return await fn(state, **kwargs)

        return wrapper

    def set_state(self) -> None:
        """
        Decide the state datatype of all nodes in the Graph.
        """
        self.state_type = State

    def add_edge(self, src: str, dest: str) -> None:
        """
        Add a direct edge between two nodes.
        """
        self.state_graph.add_edge(src, dest)

    def add_conditional_edge(self, src: str, condition: Callable[[Any], bool]) -> None:
        """
        Add a conditional edge between two nodes.
        """
        self.state_graph.add_conditional_edges(src, condition)

    def set_start_point(self, key: str) -> None:
        """
        Set the start point of the graph.
        """
        self.state_graph.set_entry_point(key)

    def set_end_point(self, key: str) -> None:
        """
        Set the end point of the graph.
        """
        self.state_graph.set_finish_point(key)

    def compile(self) -> None:
        """
        Compile the current state graph into a compiled graph.
        """
        self.compiled_graph = self.state_graph.compile()

    def add_node(self, node: "Node") -> None:
        """
        Add a node to the graph.
        """
        self.state_graph.add_node(node.name, self.gen_wrapper(node.invoke, node))
        self.all_nodes[node.name] = node

    async def ainvoke(self, input: State):
        """
        Executes the compiled graph starting from the entry point.

        :param initial_input: The initial input or state required to start the graph execution.
        :return: The final state or output after executing the graph.
        """
        if self.compiled_graph is None:
            raise Exception("Graph is not compiled yet.")
        try:
            return await self.compiled_graph.ainvoke(input)
        except Exception as e:
            syslog.error(f"The following error has occured while invoking graph:\n{e}")
            return {"agent_output": f"An error has occured"}

    async def stream(self, input: State, handle_chunk):
        has_printed = False
        async for event in self.compiled_graph.astream_events(input, version="v2"):
            kind = event["event"]
            current_node = (event.get("metadata", {})).get("langgraph_node", "")
            if kind == "on_chain_stream" and "node_core" == current_node:
                syslog(settings.ENV)
                if settings.ENV == "development" and not has_printed:
                    await handle_chunk("🤖: ")
                has_printed = True
                data = utils.dig(event, "data.chunk.agent_output", "")
                await handle_chunk(data)

    def wrapper_choose_agent(self, main_node: "Node", assistant: "Assistant") -> Callable:
        def choose_agent(state: State, **kwargs) -> str:
            compiler = kwargs["compiler"]
            assistant = kwargs["assistant"]
            agent_names = [node for node in main_node.next_nodes]
            all_next_agents = [compiler.all_nodes[agent_name] for agent_name in agent_names]
            agents_conditions = ""
            for node in all_next_agents:
                agents_conditions += f"- {node.name}: {node.conditional_prompt}\n"
            agent_names.append("node_core")
            prompt = PromptTemplate.from_template(DEFAULT_CHOOSE_AGENT_PROMPT)
            iterations = 5
            flag = False
            error_log = ""
            while iterations > 0:
                chain = prompt | assistant.llm
                res = chain.invoke(
                    input={
                        "all_agent_names": agent_names,
                        "conditions": agents_conditions,
                        "buffer_memory": assistant.buffer_memory.format_buffer_memory(assistant),
                        "query": state["input"].query,
                        "agent_output": state["agent_output"],
                        "error_log": error_log,
                    },
                    config=assistant.config,
                )

                for name in agent_names:
                    content = res if isinstance(res, str) else res.content
                    if name in content:
                        return name

                if flag is False:
                    content = res if isinstance(res, str) else res.content
                    error_log += f"Invalid output. please only choose one of the following agents {agent_names}. But you chose {content}\n"
                iterations -= 1
            syslog.warning("Jump to node_core after failing to find a next node")
            return "node_core"

        @functools.wraps(choose_agent)
        def wrapper(state: State, **kwargs) -> Callable:
            kwargs["compiler"] = self
            kwargs["assistant"] = assistant
            return choose_agent(state, **kwargs)

        return wrapper
