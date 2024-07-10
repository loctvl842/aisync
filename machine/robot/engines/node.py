from typing import Optional, List, Sequence
from ..assistants.base.assistant import Assistant
from . import prompts
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnableSequence
from .prompts import FORMAT_INSTRUCTIONS, ActionPromptTemplate, DOC_PROMPT, DEFAULT_AGENT_PROMPT_SUFFIX, DEFAULT_PROMPT_SUFFIX
from langchain.agents import AgentExecutor, create_tool_calling_agent
from core.logger import syslog
from .parser import ActionOutputParser
from langchain.agents.tools import BaseTool
import traceback

class Node:
    def __init__(
        self,
        name: str,
        prompt_prefix: Optional[str]=DEFAULT_PROMPT_SUFFIX,
        prompt_suffix: Optional[str]=DEFAULT_AGENT_PROMPT_SUFFIX,
        conditional_prompt: Optional[str]="",
        tools: Optional[List[str]]=[],
        document_names: Optional[List[str]]=[],
        interrupt_before: Optional[List[str]]=[],
        next_nodes: Optional[List[str]]=[]
    ):
        self.name = name
        self.prompt_prefix = prompt_prefix
        self.prompt_suffix = prompt_suffix
        self.conditional_prompt = conditional_prompt
        self.tools = tools
        self.document_names = document_names
        self.interrupt_before = interrupt_before
        self.next_nodes = next_nodes

    def activate(self, assistant: Assistant):
        self.assistant = assistant
        self.llm = assistant.llm
        self._suit = assistant.suit

    def create_prompt(
        self,
        tools: Sequence[BaseTool],
        format_instructions: str = FORMAT_INSTRUCTIONS,
        input_variables: Optional[List[str]] = None,
    ) -> ActionPromptTemplate:
        if input_variables is None:
            input_variables = ["input", "intermediate_steps", "buffer_memory"]

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
    
    async def execute_tools(self, agent_input, tools):
        # Prompt
        format_instructions = self.chatbot_suits.execute_hook(
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
            res = await agent_executor.ainvoke(
                input=agent_input,
                config=self.assistant.config,
            )
        except Exception as e:
            syslog.debug("Error when invoking agent_executor:\n\n", e)

        return res
    
    def execute_documents(self, agent_input):
        prompt = PromptTemplate.from_template(DOC_PROMPT)

        chain = prompt | self.llm

        res = chain.invoke(
            input={"input": agent_input["input"], "document": agent_input["document"]}, config=self.assistant.config
        )
        if isinstance(res, str):
            return res

        return res.content
    
    async def tool_output(self):
        """
        Function to execute tools and format the output to put into final prompt
        """
        # TODO: add filter by tool name
        tools = await self.assistant.tool_knowledge.find_relevant_tools(
            suit=self._suit, vectorized_input=self.vectorized_input
        )

        tool_result = ""

        if len(tools) > 0:
            try:
                res = await self.execute_tools(agent_input=input, tools=tools, assistant=self.assistant)
                if res is None:
                    tool_result = ""
                else:
                    output = res["output"]
                    tool_result = f"## Tool Output:\n `{output}`" if output else ""
            except Exception as e:
                syslog.error(f"Error when executing tools: {e}")
                traceback.print_exc()

        return tool_result

    async def persist_memory(self):
        # Run similarity search to find relevant tools
        lt_memory = await self.assistant.persist_memory.similarity_search(vectorized_input=self.vectorized_input)
        input["persist_memory"] = lt_memory["persist_memory"]

    async def document_memory(self):
        # fetch document_memory
        document_memory_output = ""
        try:
            doc = await self.assistant.document_memory.similarity_search(
                vectorized_input=self.vectorized_input,
                # TODO: add filter by document names
            )
            document_memory = self.execute_documents(
                agent_input={"input": input["input"], "document": doc}, assistant=self.assistant
            )
            document_memory_output = f"## Document Knowledge Output: `{document_memory}`"
        except Exception as e:
            syslog.error(f"Error when fetching document memory: {e}")
            traceback.print_exc()

        return document_memory_output

    def buffer_memory(self):
        return f"## Buffer Memory:\n\n{self.assistant.buffer_memory.format_buffer_memory_no_token()}"

    async def invoke(self, state):
        input = {"input": state.input}

        # Embed input
        self.vectorized_input = self._suit.execute_hook("embed_input", input=input["input"], assistant=self.assistant)

        # Document memory
        input["document_memory"] = await self.document_memory()

        # Tool Output
        input["tool_output"] = await self.tool_output()

        # Optimize Chat History
        input["buffer_memory"] = self.buffer_memory()

        res = {}
        ai_response = self._chain.invoke(input, config=self.assistant.config)
        if isinstance(ai_response, str):
            res["agent_output"] = ai_response
        else:
            res["agent_output"] = ai_response.content

        return res
        