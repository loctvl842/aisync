from langchain.schema.language_model import BaseLanguageModel
from langchain_openai import ChatOpenAI


class LLMChatOpenAI:
    model = ChatOpenAI(
        model="gpt-3.5-turbo",
        temperature=0.0,
    )


available_llms = [
    LLMChatOpenAI,
]


def get_llm_names() -> list[str]:
    return [llm.__name__ for llm in available_llms]


def get_llm(name: str) -> BaseLanguageModel:
    """
    Get an LLM by name.
    """
    for llm in available_llms:
        if name == llm.__name__:
            return llm.model
    raise ValueError(f"Unknown LLM: {name}")
