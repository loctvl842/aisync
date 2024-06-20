import re
from typing import Union

from langchain.agents import AgentOutputParser
from langchain.schema import AgentAction, AgentFinish, OutputParserException

from core.logger import syslog


class ActionOutputParser(AgentOutputParser):
    def parse(self, text: str) -> Union[AgentAction, AgentFinish]:
        # syslog.debug(text)
        if "Final Answer:" in text:
            return AgentFinish(
                return_values={"output": text.split("Final Answer:")[-1].strip()},
                log=text,
            )
        regex = r"Action: (.*?)[\n]*Action Input: ([\s\S]*)"
        match = re.search(regex, text, re.DOTALL)
        if not match:
            raise OutputParserException(f"Could not parse LLM output: `{text}`")
        action = match.group(1)
        action_input = match.group(2)
        tool_input = action_input.strip(" ").strip('"')
        if action == "none_of_the_above":
            return AgentFinish(
                return_values={
                    "output": "STOP using tools and answer user's inquiry to the best of your ability WITHOUT tools."
                },
                log=text,
            )
        # syslog.debug(f"Action: {action}")
        # syslog.debug(f"tool_input: {tool_input}")
        return AgentAction(tool=action, tool_input=tool_input, log=text)
