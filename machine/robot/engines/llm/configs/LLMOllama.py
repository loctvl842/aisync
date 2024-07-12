from typing import Type

from langchain_community.llms.ollama import Ollama
from .base import LLMConfig


class LLMOllama(LLMConfig):
    _pyclass: Type = Ollama

    model: str = "llama3"
