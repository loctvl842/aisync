from typing import Annotated, TypedDict

from langchain_google_genai import GoogleGenerativeAI, HarmBlockThreshold, HarmCategory
from langchain_openai import ChatOpenAI

from aisync.engines.graph import node
from aisync.engines.graph.definitions import State
from aisync.log import LogEngine
from aisync.env import env

log = LogEngine("mark_i")


def add_messages(messages: list[tuple[str, str]], new_messages: list[tuple[str, str]]) -> list[tuple[str, str]]:
    """Function to add a new message to the messages list."""
    messages.extend(new_messages)
    return messages


class Node1Output(TypedDict):
    private_data: str
    messages: list


@node("Input")
def node_1(state: State) -> Node1Output:
    output = {"private_data": "set by node_1", "messages": []}
    return output


class ChatbotOutput(TypedDict):
    answer: Annotated[list[dict], add_messages]
    messages: list


gemini = GoogleGenerativeAI(
    model="gemini-pro",
    google_api_key=env.GOOGLE_API_KEY,
    safety_setting={
        HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
    },
)

deepseek = ChatOpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=env.DEEPSEEK_API_KEY,
    model="deepseek/deepseek-chat",
)

print("vaicalon", env.DEEPSEEK_API_KEY)


@node(name="gemini", llm=gemini)
def helper1(state: Node1Output, llm: ChatOpenAI) -> ChatbotOutput:
    system_message = "You are a coder and problem solver expert, you explain your answer in your response"
    answer = llm.invoke([system_message] + state["messages"])
    print("Gemini: ", answer)
    return {"answer": [{"who": "gemini", "content": answer}], "messages": []}


@node(name="deepseek", llm=deepseek)
def helper2(state: Node1Output, llm: ChatOpenAI) -> ChatbotOutput:
    system_message = "You are a coder and problem solver expert, you explain your answer in your response"
    answer = llm.invoke([system_message] + state["messages"])
    print("GPT: ", answer.content)
    return {"answer": [{"who": "deepseek", "content": answer.content}], "messages": []}


@node(llm=deepseek)
def king(state: ChatbotOutput, llm: ChatOpenAI) -> State:
    ai_conversations = "\n".join(f"{a['who']}: {a['content']}" for a in state["answer"])
    system_message = (
        "You are a wise and knowledgeable coder and problem solver king who provides thoughtful answers to questions. "
        "You have 2 advisors, who offer their insights to assist you."
        "Consider their perspectives and advice, but ultimately provide your own well-reasoned response to the problem based on all context and advice. If you find their input helpful, feel free to acknowledge their contributions in your answer."
        "Response with explaination inside tag <explaination> and give the final response in tag <response>"
        "The response should follow this format:\n"
        "<explaination>Your explaination for the final response after receiving advise from advisors and explain what advisors helped, and who is better</explaination>"
        "\n"
        "<reesponse>Your response</response>"
    )
    king_decision = llm.invoke(
        [
            ("system", system_message),
            state["messages"][-1],
            ("ai", ai_conversations),
        ]
    )
    return {"messages": [("ai", king_decision)]}


def classify():
    pass


# graph = node_1 >> (helper1 & helper2) >> king
graph = helper2 >> king


if __name__ == "__main__":
    log(f"Mermaid:\n```\n{graph.to_mermaid()}\n```")
