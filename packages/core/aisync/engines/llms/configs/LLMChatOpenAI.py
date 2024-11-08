from typing import Type

from langchain_openai import ChatOpenAI

from .base import AISyncLLM


class LLMChatOpenAI(AISyncLLM):
    _pyclass: Type = ChatOpenAI

    model: str = "gpt-4o-mini"
    temperature: float = 0.0
