import os
from typing import List, Optional, Sequence

from langchain.agents import AgentExecutor, LLMSingleActionAgent
from langchain.agents.tools import BaseTool

from ..manager import Manager
import prompts
from .parser import ActionOutputParser

should_log = (os.getenv("ENV") or "production").lower() == "development"


class AgentManager:
    """
    This is a service managed by Beast.
    """

    def __init__(self) -> None:
        self.chatbot_suits = Manager().suits["chatbot"]
        self.chain = None

    def create_prompt(
        self,
        tools: Sequence[BaseTool],
        format_instructions: str = prompts.FORMAT_INSTRUCTIONS,
        input_variables: Optional[List[str]] = None,
    ) -> prompts.ActionPromptTemplate:
        if input_variables is None:
            input_variables = ["input", "intermediate_steps", "chat_history"]

        return prompts.ActionPromptTemplate(
            template=format_instructions,
            input_variables=input_variables,
            tools=tools,
        )

    def execute_tools(self, agent_input, tools, chatbot):
        allowed_tools = [tool.name for tool in tools]

        # Prompt
        format_instructions = self.chatbot_suits.execute_hook(
            "build_format_instructions", default=prompts.FORMAT_INSTRUCTIONS, chatbot=chatbot
        )
        prompt = self.create_prompt(tools=tools, format_instructions=format_instructions)

        # Chain
        chain = prompt | chatbot.llm

        # Agent
        agent = LLMSingleActionAgent(
            llm_chain=chain,
            output_parser=ActionOutputParser(),
            stop=["Observation:"],
            allowed_tools=allowed_tools,
        )

        # Executor
        # Using return_intermediate_steps=True here because we want to see the intermediate steps of the agent.
        # We'll handle response in the talk chain.
        agent_executor = AgentExecutor.from_agent_and_tools(
            agent=agent, tools=tools, return_intermediate_steps=True, handle_parsing_errors=True, verbose=should_log
        )
        res = agent_executor(agent_input)
        return res