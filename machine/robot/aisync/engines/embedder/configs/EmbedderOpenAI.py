from typing import Type

from langchain_openai import OpenAIEmbeddings

from .base import AscEmbedderConfig


class EmbedderOpenAI(AscEmbedderConfig):
    _pyclass: Type = OpenAIEmbeddings

    model: str = "text-embedding-3-small"
    dimensions: int = 768
