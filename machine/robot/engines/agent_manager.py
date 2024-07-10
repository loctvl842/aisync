import os
from typing import List, Optional, Sequence

from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain.agents.tools import BaseTool
from langchain_core.prompts import PromptTemplate

from core.logger import syslog

from ..manager import Manager
from .parser import ActionOutputParser
from .prompts import FORMAT_INSTRUCTIONS, ActionPromptTemplate

should_log = (os.getenv("ENV") or "production").lower() == "development"


class AgentManager:
    """
    This is a service managed by Beast.
    """

    def __init__(self) -> None:
        # Change to suit mark_ii_4all if you want to use GPT4All, rockship_chatbot for Rockship Chatbot
        self.chatbot_suits = Manager().suits["mark_i"]
        self.chain = None

    def switch_suit(self, suit: str):
        self.chatbot_suits = Manager().suits[suit]

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

    def create_tool_agent(self, llm, tools, prompt):
        """
        A version of create_tool_calling_agent that does not require the LLM to bind tools.
        Enable usage with Langchain's AgentExecutor.
        """
        if not hasattr(llm, "add_tools"):
            raise ValueError(
                "This function requires a .add_tools method be implemented on the LLM.",
            )
        llm.add_tools(tools)

        agent = (
            {
                "input": lambda x: x["input"],
                "buffer_memory": lambda x: x["buffer_memory"],
                "intermediate_steps": lambda x: x["intermediate_steps"],
            }
            | prompt
            | llm
            | ActionOutputParser()
        )
        return agent

    async def execute_tools(self, agent_input, tools, assistant):
        # Prompt
        format_instructions = self.chatbot_suits.execute_hook(
            "build_format_instructions", default=FORMAT_INSTRUCTIONS, assistant=assistant
        )
        prompt = self.create_prompt(
            tools=tools,
            format_instructions=format_instructions,
        )
        # Agent
        agent = None
        if hasattr(assistant.llm, "bind_tools"):
            agent = create_tool_calling_agent(
                llm=assistant.llm,
                prompt=prompt,
                tools=tools,
            )
        else:
            agent = self.create_tool_agent(llm=assistant.llm, tools=tools, prompt=prompt)

        # Executor
        # Using return_intermediate_steps=True here because we want to see the intermediate steps of the agent.
        # We'll handle response in the talk chain.
        agent_executor = AgentExecutor.from_agent_and_tools(
            agent=agent, tools=tools, return_intermediate_steps=True, handle_parsing_errors=True, verbose=should_log
        )
        res = None
        try:
            res = await agent_executor.ainvoke(
                input=agent_input,
                config=assistant.config,
            )
        except Exception as e:
            syslog.debug("Error when invoking agent_executor:\n\n", e)

        # Remove tools in case it's CustomizedGPT4All
        if hasattr(assistant.llm, "remove_tools"):
            assistant.llm.remove_tools()

        return res

    def execute_documents(self, agent_input, assistant):
        prompt = self.chatbot_suits.execute_hook("build_prompt_from_docs", assistant=assistant)
        prompt = PromptTemplate.from_template(prompt)

        chain = prompt | assistant.llm

        res = chain.invoke(
            input={"input": agent_input["input"], "document": agent_input["document"]}, config=assistant.config
        )
        if isinstance(res, str):
            return res

        return res.content
