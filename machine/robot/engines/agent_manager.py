import os
from typing import List, Optional, Sequence, TypedDict, Dict, Any, Union

from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain.agents.tools import BaseTool
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.runnables import RunnableConfig

from ..manager import Manager
from .parser import ActionOutputParser
from .prompts import FORMAT_INSTRUCTIONS, ActionPromptTemplate
from core.logger import syslog


should_log = (os.getenv("ENV") or "production").lower() == "development"


class AgentManager:
    """
    This is a service managed by Beast.
    """

    def __init__(self) -> None:
        # Temporarily change suit for GPT4All
        self.chatbot_suits = Manager().suits["mark_ii_4all"]
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
        def process_input(str_request: str):
            try:
                str_request = str_request[str_request.index('{'):].strip()
                syslog.info(f'\nProcessing Input Stage: {str_request}\n')
                res = JsonOutputParser().parse(str_request)
                if res is None:
                    return f"Invalid input. Please try again.\n {e}"
                return res
            except Exception as e:
                return f"Invalid input. Please try again.\n {e}"
            
        
        def invoke_tool(
                input: Union[str, dict], config: Optional[RunnableConfig] = None
            ):
                
                """A function that we can use the perform a tool invocation.

                Args:
                    tool_call_request: a dict that contains the keys name and arguments.
                        The name must match the name of a tool that exists.
                        The arguments are the arguments to that tool.
                    config: This is configuration information that LangChain uses that contains
                        things like callbacks, metadata, etc.See LCEL documentation about RunnableConfig.

                Returns:
                    output from the requested tool
                """
                if isinstance(input, str):
                    return f"The input: ```\n{input}\n```\n was of an invalid dictionary format. Please try again.\n"
                try: 
                    tool_call_request = input
                    tool_name_to_tool = {tool.name: tool for tool in tools}
                    name = tool_call_request["name"]
                    requested_tool = tool_name_to_tool[name]
                    res = requested_tool.invoke(tool_call_request["arguments"], config=config)
                    syslog.info(res)
                    return f"Action: {name}\nAction Input: {tool_call_request['arguments']}\nFinal Answer: {res}"
                except Exception as e:
                    return f"Action: Unidentified\nAction Input: Unidentified\nObservation: {e}"

        agent = (
            {
                "input": lambda x: x["input"],
                "chat_history": lambda x: x["chat_history"],
                "intermediate_steps": lambda x: x["intermediate_steps"],
            }
            | prompt
            | llm
            | process_input
            | invoke_tool 
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
        res = agent_executor.invoke(
            input=agent_input,
            config=assistant.config,
        )
        return res
