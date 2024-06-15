from typing import Type

from langchain_openai import OpenAIEmbeddings

from .base import EmbedderConfig


class EmbedderOpenAI(EmbedderConfig):
    _pyclass: Type = OpenAIEmbeddings

    model: str = "text-embedding-3-small"
    dimensions: int =1024