from typing import Type

from langchain_openai import ChatOpenAI

from .base import AisyncLLM


class LLMChatOpenAI(AisyncLLM):
    _pyclass: Type = ChatOpenAI

    model: str = "gpt-4o-mini"
    temperature: float = 0.0
