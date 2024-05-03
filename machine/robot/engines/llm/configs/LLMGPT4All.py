from typing import Type
from .base import LLMConfig
from langchain_community.llms import GPT4All


class LLMGPT4All(LLMConfig):
    _pyclass: Type = GPT4All

    model: str = "../gpt4all/mistral-7b-openorca.gguf2.Q4_0.gguf"
