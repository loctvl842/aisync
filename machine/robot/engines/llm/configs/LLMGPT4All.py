from typing import Type

from langchain_community.llms import GPT4All

from .base import LLMConfig


class LLMGPT4All(LLMConfig):
    _pyclass: Type = GPT4All

    model: str = "../gpt4all/mistral-7b-openorca.gguf2.Q4_0.gguf"
    n_threads: int = 8
    temp: float = 0.4
