from typing import Type

from langchain_community.llms.ollama import Ollama

from .base import AisyncLLM


class LLMOllama(AisyncLLM):
    _pyclass: Type = Ollama

    model: str = "llama3"
