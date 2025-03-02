from typing import Type

from aisync.engines.llms.base import AISyncLLM
from langchain_openai import ChatOpenAI


class LLMChatOpenAI(AISyncLLM):
    _pyclass: Type = ChatOpenAI

    model: str = "gpt-4o-mini"
    temperature: float = 0.0
