from typing import Type

from langchain_google_vertexai import VertexAIEmbeddings

from .base import AISyncEmbedder


class EmbedderGoogleVertexAI(AISyncEmbedder):
    _pyclass: Type = VertexAIEmbeddings
