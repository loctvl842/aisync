from typing import Type

from langchain_google_vertexai import VertexAIEmbeddings

from .base import EmbedderConfig


class EmbedderGoogleVertexAI(EmbedderConfig):
    _pyclass: Type = VertexAIEmbeddings
