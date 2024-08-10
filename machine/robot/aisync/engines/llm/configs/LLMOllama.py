from typing import Type

from langchain_community.llms.ollama import Ollama

from .base import AISyncLLM


class LLMOllama(AISyncLLM):
    _pyclass: Type = Ollama

    model: str = "llama3"
