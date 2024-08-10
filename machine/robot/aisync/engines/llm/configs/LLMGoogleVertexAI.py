from typing import Type

from langchain_google_vertexai import ChatVertexAI

from .base import AISyncLLM


class LLMGoogleVertexAI(AISyncLLM):
    _pyclass: Type = ChatVertexAI

    model_name: str = "gemini-pro"
    project: str = "aisync-423812"
