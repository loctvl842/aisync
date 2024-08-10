from typing import Type

from langchain_ollama import ChatOllama

from .base import AISyncLLM


class LLMChatOllama(AISyncLLM):
    _pyclass: Type = ChatOllama

    model: str = "llama3"
