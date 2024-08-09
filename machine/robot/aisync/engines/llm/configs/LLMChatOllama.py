from typing import Type

from langchain_ollama import ChatOllama

from .base import AisyncLLM


class LLMChatOllama(AisyncLLM):
    _pyclass: Type = ChatOllama

    model: str = "llama3"
