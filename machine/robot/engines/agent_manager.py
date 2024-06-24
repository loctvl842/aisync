import os
from typing import List, Optional, Sequence

from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain.agents.tools import BaseTool

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
        self.chatbot_suits = Manager().suits["rockship_chatbot"]
        self.chain = None

    def create_prompt(
        self,
        tools: Sequence[BaseTool],
        format_instructions: str = FORMAT_INSTRUCTIONS,
        input_variables: Optional[List[str]] = None,
    ) -> ActionPromptTemplate:
        if input_variables is None:
            input_variables = ["input", "intermediate_steps", "chat_history"]

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
                "chat_history": lambda x: x["chat_history"],
                "intermediate_steps": lambda x: x["intermediate_steps"],
            }
            | prompt
            | llm
            | ActionOutputParser()
        )
        return agent

    def execute_tools(self, agent_input, tools, assistant):
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
            res = agent_executor.invoke(
                input=agent_input,
                config=assistant.config,
            )
        except Exception as e:
            syslog.debug("Error when invoking agent_executor:\n\n", e)

        # Remove tools in case it's CustomizedGPT4All
        if hasattr(assistant.llm, "remove_tools"):
            assistant.llm.remove_tools()

        return res
