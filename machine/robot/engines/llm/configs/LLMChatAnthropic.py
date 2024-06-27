from typing import Type

from langchain_anthropic import ChatAnthropic

from .base import LLMConfig


class LLMChatAnthropic(LLMConfig):
    _pyclass: Type = ChatAnthropic

    model: str = "claude-3-haiku-20240307"
    temperature: float = 0.1
    
