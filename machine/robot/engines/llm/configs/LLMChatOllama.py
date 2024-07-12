from typing import Type

from langchain_community.chat_models.ollama import ChatOllama
from .base import LLMConfig


class LLMOllama(LLMConfig):
    _pyclass: Type = ChatOllama

    model: str = "llama3"
