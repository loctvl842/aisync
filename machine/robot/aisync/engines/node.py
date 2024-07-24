import traceback
from typing import TYPE_CHECKING, List, Optional, Sequence

from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain.agents.tools import BaseTool
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnableSequence

from core.logger import syslog
from core.utils.decorators import stopwatch

from ..assistants.base.assistant import Assistant
from . import prompts
from .llm import get_llm_by_name
from .parser import ActionOutputParser
from .prompts import (
    DEFAULT_AGENT_PROMPT_SUFFIX,
    DEFAULT_PROMPT_PREFIX,
    DEFAULT_PROMPT_SUFFIX,
    DOC_PROMPT,
    FORMAT_INSTRUCTIONS,
    ActionPromptTemplate,
)

if TYPE_CHECKING:
    from ..assistants.base.assistant import Assistant


class Node:
    def __init__(
        self,
        name: str,
        prompt_prefix: Optional[str] = DEFAULT_PROMPT_PREFIX,
        prompt_suffix: Optional[str] = DEFAULT_AGENT_PROMPT_SUFFIX,
        conditional_prompt: Optional[str] = "",
        tools: Optional[List[str]] = [],
        document_names: Optional[List[str]] = [],
        interrupt_before: Optional[List[str]] = [],
        next_nodes: Optional[List[str]] = [],
        llm_name: Optional[str] = "LLMChatOpenAI",
    ):
        self.name = name
        self.prompt_prefix = prompt_prefix
        self.prompt_suffix = prompt_suffix
        self.conditional_prompt = conditional_prompt
        self.tools = tools
        self.document_names = document_names
        self.interrupt_before = interrupt_before
        self.next_nodes = next_nodes
        self.llm_name = llm_name

    def change_llm(self, llm_name: str) -> None:
        cfg_cls = get_llm_by_name(llm_name)
        if cfg_cls is None:
            cfg_cls = get_llm_by_name("LLMChatOpenAI")
            syslog.error(f"LLM {llm_name} not found. Using LLMChatOpenAI instead.")
        default_cfg = cfg_cls().model_dump()
        self.llm = cfg_cls.get_llm(default_cfg)

    def activate(self, assistant: "Assistant", should_use_assistant_llm: Optional[bool] = False) -> None:
        self.assistant = assistant
        self._suit = assistant.suit
        if should_use_assistant_llm:
            self.llm = assistant.llm
        else:
            self.change_llm(self.llm_name)
        self._chain = self._make_chain()

    def create_prompt(
        self,
        tools: Sequence[BaseTool],
        format_instructions: str = FORMAT_INSTRUCTIONS,
        input_variables: Optional[List[str]] = None,
    ) -> ActionPromptTemplate:
        if input_variables is None:
            input_variables = ["query", "intermediate_steps", "buffer_memory"]

        return ActionPromptTemplate(
            template=format_instructions,
            input_variables=input_variables,
            tools=tools,
            partial_variables={"agent_scratchpad": []},
            output_parser=ActionOutputParser(),
        )

    def _make_prompt(
        self,
        prefix: str = prompts.DEFAULT_PROMPT_PREFIX,
        suffix: str = prompts.DEFAULT_PROMPT_SUFFIX,
        input_variables: Optional[List[str]] = None,
    ):
        template = "\n\n".join([prefix, suffix])
        self.template = template
        if input_variables is None:
            input_variables = ["input", "buffer_memory", "document_memory", "tool_output"]
        return PromptTemplate(
            template=template,
            input_variables=input_variables,
        )

    def _make_chain(self) -> RunnableSequence:
        # Prepare prompt
        self.prompt = self._make_prompt(prefix=self.prompt_prefix, suffix=self.prompt_suffix)
        chain = self.prompt | self.llm
        return chain

    async def execute_tools(self, agent_input, tools) -> dict:
        # Prompt
        format_instructions = self._suit.execute_hook(
            "build_format_instructions", default=FORMAT_INSTRUCTIONS, assistant=self.assistant
        )
        prompt = self.create_prompt(
            tools=tools,
            format_instructions=format_instructions,
        )
        # Agent
        agent = None
        if hasattr(self.llm, "bind_tools"):
            agent = create_tool_calling_agent(
                llm=self.llm,
                prompt=prompt,
                tools=tools,
            )
        else:
            raise ValueError("This function requires a .bind_tools method be implemented on the LLM.")
        # Executor
        # Using return_intermediate_steps=True here because we want to see the intermediate steps of the agent.
        # We'll handle response in the talk chain.
        agent_executor = AgentExecutor.from_agent_and_tools(
            agent=agent, tools=tools, return_intermediate_steps=True, handle_parsing_errors=True, verbose=False
        )
        res = None
        try:
            # syslog.info(agent_input)
            res = await agent_executor.ainvoke(
                input=agent_input,
                config=self.assistant.config,
            )
        except Exception as e:
            syslog.error("Error when invoking agent_executor:\n\n", e)

        return res

    @stopwatch(prefix="summarize_document_chain")
    async def execute_documents(self, agent_input: dict) -> str:
        """
        Function to summarize understanding from documents
        """
        template = self._suit.execute_hook("build_prompt_from_docs", default=DOC_PROMPT, assistant=self.assistant)
        prompt = PromptTemplate.from_template(template)

        chain = prompt | self.llm

        res = chain.invoke(input=agent_input, config=self.assistant.config)
        if isinstance(res, str):
            return res

        return res.content

    @stopwatch(prefix="Using tools")
    async def tool_output(self, input: dict, vectorized_input: List[float]) -> str:
        """
        Function to execute tools and format the output to put into final prompt
        """
        tools = await self.assistant.tool_knowledge.find_relevant_tools(
            tools=self._suit.tools,
            vectorized_input=vectorized_input,
            tools_access=self.tools,
        )

        tool_result = ""

        if len(tools) > 0:
            try:
                res = await self.execute_tools(agent_input=input, tools=tools)
                if res is None:
                    tool_result = ""
                else:
                    output = res["output"]
                    tool_result = f"## Tool Output:\n `{output}`" if output else ""
            except Exception as e:
                syslog.error(f"Error when executing tools: {e}")
                traceback.print_exc()

        return tool_result

    async def persist_memory(self) -> str:
        """
        Retrieve relevant persistent memory from past sessions
        """
        lt_memory = await self.assistant.persist_memory.similarity_search(vectorized_input=self.vectorized_input)
        return lt_memory["persist_memory"]

    async def document_memory(self, vectorized_input: List[float], query: str) -> str:
        """
        Retrieve relevant document
        """
        document_memory_output = ""
        try:
            doc = await self.assistant.document_memory.similarity_search(
                vectorized_input=vectorized_input,
                document_name=self.document_names,
            )
            document_memory = await self.execute_documents(agent_input={"query": query, "document": doc})
            document_memory_output = f"## Document Knowledge Output: `{document_memory}`"
        except Exception as e:
            syslog.error(f"Error when fetching document memory: {e}")
            traceback.print_exc()

        return document_memory_output

    def buffer_memory(self):
        """
        Retrieve buffer memory
        """
        return f"## Buffer Memory:\n\n{self.assistant.buffer_memory.format_buffer_memory(self.assistant)}"

    @stopwatch(prefix="setup_input")
    async def setup_input(self, state: dict) -> dict:
        input = state["input"].model_dump()
        # Embed input
        self.vectorized_input = self._suit.execute_hook(
            "embed_input", input=state["input"], assistant=self.assistant, default=[0] * 768
        )

        # Optimize Chat History
        input["buffer_memory"] = self.buffer_memory()

        import asyncio

        tool_task = asyncio.create_task(self.tool_output(input, vectorized_input=self.vectorized_input))
        document_task = asyncio.create_task(
            self.document_memory(vectorized_input=self.vectorized_input, query=input["query"])
        )
        tool_output_res, document_output_res = await asyncio.gather(tool_task, document_task)

        input["tool_output"] = tool_output_res
        input["document_memory"] = document_output_res

        return input

    def find_missing_var(self, input: dict, prompt: str) -> set:
        """
        Function to validate prompt
        """
        from langchain_core.prompts import get_template_variables

        input_variables = get_template_variables(template=prompt, template_format="f-string")
        available_input_vars = set(input.keys())
        missing_vars = set()
        for v in input_variables:
            if v not in available_input_vars:
                missing_vars.add(v)
        return missing_vars

    @staticmethod
    @stopwatch(prefix="node_running")
    async def invoke(state, **kwargs):
        cur_node = kwargs["cur_node"]
        assistant = cur_node.assistant
        syslog.info(f"Invoking node: {cur_node.name}")
        syslog.info(f"Using model {cur_node.llm.model if hasattr(cur_node.llm, 'model') else cur_node.llm.model_name}")
        input = await cur_node.setup_input(state)

        syslog(input)

        missing_vars = cur_node.find_missing_var(input=input, prompt=cur_node.template)

        if len(missing_vars) > 0:
            raise ValueError(f"Invalid prompt for node: {cur_node.name}\nReason: Missing variables {missing_vars}")

        res = {}
        try:
            ai_response = cur_node._chain.invoke(input, config=cur_node.assistant.config)
            # syslog.info(ai_response)
            if isinstance(ai_response, str):
                res["agent_output"] = ai_response
            else:
                res["agent_output"] = ai_response.content
        except Exception as e:
            syslog.error(f"Error when invoking node: {e}")
            traceback.print_exc()
            res["agent_output"] = "Failed to execute\n"
        # assistant.buffer_memory.save_message(cur_node.name, res["agent_output"])
        return res
