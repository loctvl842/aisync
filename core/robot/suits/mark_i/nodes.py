# import os
from typing import Annotated, TypedDict

from langchain_openai import ChatOpenAI

# from langgraph.graph import add_messages
from core.robot.aisync.decorators import node
from core.robot.aisync.decorators.graph import graph
from core.robot.aisync.decorators.hook import hook
from core.robot.aisync.engines.workflow import State
from core.robot.aisync.log import log


def add_messages(messages: list[tuple[str, str]], new_messages: list[tuple[str, str]]) -> list[tuple[str, str]]:
    """Function to add a new message to the messages list."""
    messages.extend(new_messages)
    return messages


@hook
def before_read_message(input: str):
    return {"messages": [("human", input)]}


@hook
def before_send_message(message):
    if message[1]["langgraph_node"] == "king":
        return message[0].content
    # return message['messages'][-1][1].content
    # return message


llm = ChatOpenAI(model="gpt-3.5-turbo")


class Node1Output(TypedDict):
    private_data: str
    messages: list


@node("A")
def node_1(state: State) -> Node1Output:
    output = {"private_data": "set by node_1", "messages": []}
    return output


class ChatbotOutput(TypedDict):
    answer: Annotated[list[dict], add_messages]
    messages: list


@node(name="gpt35", llm=ChatOpenAI(model="gpt-3.5-turbo"))
def helper1(state: Node1Output, llm: ChatOpenAI) -> ChatbotOutput:
    system_message = "You are a coder and problem solver expert"
    answer = llm.invoke([system_message] + state["messages"])
    return {"answer": [{"who": "gpt-3.5-turbo", "content": answer.content}], "messages": []}


@node(name="gpt4omini", llm=ChatOpenAI(model="gpt-4o-mini"))
def helper2(state: Node1Output, llm: ChatOpenAI) -> ChatbotOutput:
    system_message = "You are a coder and problem solver expert"
    answer = llm.invoke([system_message] + state["messages"])
    return {"answer": [{"who": "gpt-4o-mini", "content": answer.content}], "messages": []}


@node(llm=ChatOpenAI(model="gpt-4o-mini"))
def king(state: ChatbotOutput, llm: ChatOpenAI) -> State:
    ai_conversations = "\n".join(f"{a['who']}: {a['content']}" for a in state["answer"])
    log(ai_conversations)
    system_message = (
        "You are a wise and knowledgeable coder and problem solver king who provides thoughtful answers to questions. "
        "You have 2 advisors, who offer their insights to assist you."
        "Consider their perspectives and advice, but ultimately provide your own well-reasoned response to the problem based on all context and advice. If you find their input helpful, feel free to acknowledge their contributions in your answer."
    )
    king_decision = llm.invoke(
        [
            (
                "system",
                system_message,
            ),
            state["messages"][-1],
            ("ai", ai_conversations),
        ]
    )
    return {"messages": [("ai", king_decision)]}


@graph
def main():
    return """
graph TD
    START --> A
    A --> gpt35
    A --> gpt4omini
    gpt35 --> king
    gpt4omini --> king
    king --> END
    """


__all__ = ["main"]
