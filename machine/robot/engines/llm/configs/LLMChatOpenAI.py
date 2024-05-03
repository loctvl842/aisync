from typing import Type

from langchain_openai import ChatOpenAI

from .base import LLMConfig


class LLMChatOpenAI(LLMConfig):
    _pyclass: Type = ChatOpenAI

    model: str = "gpt-3.5-turbo"
    temperature: float = 0.0
