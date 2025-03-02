from langchain_openai import ChatOpenAI

from aisync.engines.graph import hook, node
from aisync.engines.workflow import State


def add_messages(messages: list[tuple[str, str]], new_messages: list[tuple[str, str]]) -> list[tuple[str, str]]:
    """Function to add a new message to the messages list."""
    return messages + new_messages

@hook
def before_read_message(input: str):
    return {"messages": [("human", input)]}

@hook
def before_send_message(message):
    if message[1]["langgraph_node"] == "bot":
        return message[0].content


@node(name="bot", llm=ChatOpenAI(model="gpt-3.5-turbo"))
def chatbot(state: State, llm: ChatOpenAI) -> State:
    respond = llm.invoke(state["messages"])
    return {"messages": [respond]}
