import os
from typing import Annotated, TypedDict

from langchain_openai import ChatOpenAI

from aisync.decorators import node

# from aisync.engines.workflow import State
from aisync.engines.graph import State
from aisync.env import env
from aisync.log import log


def add_messages(messages: list[tuple[str, str]], new_messages: list[tuple[str, str]]) -> list[tuple[str, str]]:
    """Function to add a new message to the messages list."""
    messages.extend(new_messages)
    return messages


# Set OPENAI_API_KEY in your environment
os.environ["OPENAI_API_KEY"] = env.OPENAI_API_KEY


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


graph = node_1 >> (helper1 & helper2) >> king

if __name__ == "__main__":
    log(f"Mermaid:\n```\n{graph.to_mermaid()}\n```")
