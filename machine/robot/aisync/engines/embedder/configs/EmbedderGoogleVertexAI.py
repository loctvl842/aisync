from typing import Type

from langchain_google_vertexai import VertexAIEmbeddings

from .base import AscEmbedderConfig


class EmbedderGoogleVertexAI(AscEmbedderConfig):
    _pyclass: Type = VertexAIEmbeddings
