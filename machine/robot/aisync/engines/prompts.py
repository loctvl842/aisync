from typing import Any, Dict, Sequence

from langchain.agents.tools import BaseTool
from langchain.prompts.base import StringPromptTemplate


class ActionPromptTemplate(StringPromptTemplate):
    template: str
    input_variables: list[str]
    tools: Sequence[BaseTool]
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


FORMAT_INSTRUCTIONS = """Answer the following question: `{query}`.

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
Question: {query}
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
Human: {query}
AI:"""


DEFAULT_AGENT_PROMPT_SUFFIX = """
Effectively use your context to answer queries.
- Consider all information available from context and effectively combine them in order to respond to the query.
Your answer to Human should be focused on the following context:

Begin!

# Context:

{buffer_memory}

{document_memory}

{tool_output}
"""

CLASSIFIER_PROMPT = """Detect the topic of the following question: `{query}`.
Only output one of the following topics:

TOPICS:
------

Here are available topics:
{available_topics}
- `Other` (default): if the question is not about any of the above topics.

Begin!
Question: {input}"""

DOC_PROMPT = """
    This is the context: `{query}`.
    Ignore all document knowledge that are not relevant to the context.
    Output any relevant information that might be relevant to the context using the following document knowledge:

    {document}
    """


# DEFAULT_CHOOSE_AGENT_PROMPT = """
# # Character
# You're an expertise in conducting user intent analysis.
# You have the outstanding capability of figuring out the users' ask and directing them to the apt agent promptly for their inquiries.
# Your answer must be in format: [Agent Name], Agent Name include: {all_agent_names}
#
# {conditions}
# - node_core: Used when the current agent output is sufficient to answer user's query
# ### Skill 1: Personal Consulting Situation
# - Understand the consulting situation with the user.
# - Fill in 'scenario' in the database reflecting the situation.
#
# ### Skill 2: Route them to relevant agents
# - Swiftly connect the users to the appropriate agent in line with their inquiries after comprehending their intents.
#
# ### Skill 3: Know when to stop
# - Taking into consideration the query and the agent output, if you deem that it is satisfiable, route them directly to node_core
#
# ## Constraints
# - Your singular objective is to understand the users' intent and route their inquiries to the relevant agents.
# - Refrain from trying to answer any specific questions raised by the users, but instead guide them to the most suitable agent who can handle the inquiry.
#
# Begin!
# Query: {input}
# Agent Output: {agent_output}
# Error Log: {error_log}
# # """

DEFAULT_CHOOSE_AGENT_PROMPT = """
You are a supervisor tasked with managing a conversation between the

following workers:  {all_agent_names}. Given the following user request,
respond with the worker to act next. Each worker will perform a
task and respond with their results and status. When finished,
respond with FINISH.

Given the context and workers, who should act next?

# Workers

{conditions}

- node_core: Used when the current agent output is sufficient to answer user's query

# Context

{buffer_memory}

{agent_output}

# Current conversation:
Human: {query}
AI:
"""


DEFAULT_BS_DETECTOR_SELF_REFLECTION_PROMPT = """
    You are an expert at self-reflecting your own answers.
    # Query: 
    ```
    {assistant_prompt}
    ```
    # Proposed Answer: 
    ```
    {answer}
    ```
    Are you really sure the proposed answer is
    {top_choice}? Choose again: {choices}. 
    # The output should strictly use the following template: 
    ```
    explanation: [insert analysis]
    answer: [choose one option from among choices {choices}]
    ```
"""
