from typing import List

from langchain.agents.tools import BaseTool
from langchain.prompts.base import StringPromptTemplate


class ActionPromptTemplate(StringPromptTemplate):
    template: str
    input_variables: list[str]
    tools: List[BaseTool]

    def format(self, **kwargs) -> str:
        intermediate_steps = kwargs.pop("intermediate_steps")
        thoughts = ""
        for action, observation in intermediate_steps:
            thoughts += action.log
            thoughts += f"\nObservation: {observation}\n"
        kwargs["agent_scratchpad"] = thoughts
        kwargs["tools"] = "\n".join([f"> `{tool.name}`: {tool.description}" for tool in self.tools])
        kwargs["allowed_tools"] = ", ".join([f"`{tool.name}`" for tool in self.tools])
        return self.template.format(**kwargs)


FORMAT_INSTRUCTIONS = """Answer the following question: `{input}`.

TOOLS:
------

You has access to the following tools:
{tools}
> `none_of_the_above`: none_of_the_above(too_input=None) - Use this tool if none of the above tools help.
    Input is always None.

To use a tool, you MUST use the following formats:

```
Action: the action to take, should be one of [{allowed_tools}, `none_of_the_above`]
Action Input: the input to the action
Observation: the result of the action
```

When you have a final answer to say to the Human, you MUST use the format:

```
Final Answer: [your response here]
```

Begin!
## Previous conversation history:

{chat_history}
Question: {input}
{agent_scratchpad}"""


DEFAULT_PROMPT_PREFIX = """# Character
You serve as an intelligent assistant who possesses many skills and knowledge areas.
You have proven your competence by passing the Turing test. You are known for your friendly and approachable manner.
You answer to Human shortly and with a focus on the following context:
"""

DEFAULT_PROMPT_SUFFIX = """Begin!

# Context:

{tool_output}

## Previous conversation history:

{chat_history}

## Current conversation:
Human: {input}
AI:"""

CLASSIFIER_PROMPT = """Detect the topic of the following question: `{input}`.
Only output one of the following topics:

TOPICS:
------

Here are available topics:
{available_topics}
- `Other` (default): if the question is not about any of the above topics.

Begin!
Question: {input}"""
