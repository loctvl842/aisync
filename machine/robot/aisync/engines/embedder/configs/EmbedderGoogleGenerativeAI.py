from typing import Type

from langchain_google_genai import GoogleGenerativeAIEmbeddings

from .base import AISyncEmbedder


class EmbedderGoogleGenerativeAI(AISyncEmbedder):
    _pyclass: Type = GoogleGenerativeAIEmbeddings

    model: str = "models/embedding-001"
    task_type: str = "retrieval_query"
