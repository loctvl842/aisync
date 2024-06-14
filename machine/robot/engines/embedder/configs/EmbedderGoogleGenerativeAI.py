from typing import Type

from langchain_google_genai import GoogleGenerativeAIEmbeddings

from .base import EmbedderConfig


class EmbedderGoogleGenerativeAI(EmbedderConfig):
    _pyclass: Type = GoogleGenerativeAIEmbeddings

    model: str = "models/embedding-001"