import os
from typing import List, Optional, Sequence

from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain.agents.tools import BaseTool

from .parser import ActionOutputParser
from .prompts import FORMAT_INSTRUCTIONS, ActionPromptTemplate
from ..manager import Manager



should_log = (os.getenv("ENV") or "production").lower() == "development"


class AgentManager:
    """
    This is a service managed by Beast.
    """

    def __init__(self) -> None:
        self.chatbot_suits = Manager().suits["mark_i"]
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

    def execute_tools(self, agent_input, tools, assistant):
        allowed_tools = [tool.name for tool in tools]

        # Prompt
        format_instructions = self.chatbot_suits.execute_hook(
            "build_format_instructions", default=FORMAT_INSTRUCTIONS, assistant=assistant
        )
        prompt = self.create_prompt(
            tools=tools, 
            format_instructions=format_instructions, 
        )
        # Agent
        agent = create_tool_calling_agent(
            llm=assistant.llm, 
            prompt=prompt,
            tools=tools,
        )

        # Executor
        # Using return_intermediate_steps=True here because we want to see the intermediate steps of the agent.
        # We'll handle response in the talk chain.
        agent_executor = AgentExecutor.from_agent_and_tools(
            agent=agent, tools=tools, return_intermediate_steps=True, handle_parsing_errors=True, verbose=should_log
        )
        res = agent_executor.invoke(
            input=agent_input,
            config=assistant.config,
        )
        return res