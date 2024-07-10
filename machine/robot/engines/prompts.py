from typing import Any, Dict, List

from langchain.agents.tools import BaseTool
from langchain.prompts.base import StringPromptTemplate


class ActionPromptTemplate(StringPromptTemplate):
    template: str
    input_variables: list[str]
    tools: List[BaseTool]
    partial_variables: Dict[str, Any]

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

You have access to the following tools:
{tools}

To use a tool, you MUST use the following formats:

```
Action: the action to take, should be one of [{allowed_tools}]
Action Input: the input to the action
Observation: the result of the action
```

When you have a final answer to say to the Human, you MUST use the format:

```
I used the following tool: [tool_name]
Its purpose is: [tool_description]
My answer is: [answer]
```

Begin!
## Previous conversation history:

{buffer_memory}
Question: {input}
{agent_scratchpad}"""


DEFAULT_PROMPT_PREFIX = """# Character
You serve as an intelligent assistant who possesses many skills and knowledge areas.
You have proven your competence by passing the Turing test. You are known for your friendly and approachable manner.
You have the following skills:

# Skills:
## Skill 1: Effectively use your context to answer queries.
- Consider all information available from context and effectively combine them in order to answer user's query.
Your answer to Human should be focused on the following context:
"""

DEFAULT_PROMPT_SUFFIX = """Begin!

# Context:

## Buffer Memory:

{buffer_memory}

{document_memory}

{persist_memory}

{tool_output}

# Current conversation:
Human: {input}
AI:"""


DEFAULT_AGENT_PROMPT_SUFFIX = """Begin!

# Context:

{buffer_memory}

{document_memory}

{tool_output}
"""
  
CLASSIFIER_PROMPT = """Detect the topic of the following question: `{input}`.
Only output one of the following topics:

TOPICS:
------

Here are available topics:
{available_topics}
- `Other` (default): if the question is not about any of the above topics.

Begin!
Question: {input}"""

DOC_PROMPT = """
    This is the context: `{input}`.
    Ignore all document knowledge that are not relevant to the context.
    Output any relevant information that might be relevant to the context using the following document knowledge:

    {document}
    """