from typing import Type

from langchain_ollama import ChatOllama

from .base import LLMConfig


class LLMChatOllama(LLMConfig):
    _pyclass: Type = ChatOllama

    model: str = "llama3"
