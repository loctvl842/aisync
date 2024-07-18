from typing import List, Type

from sentence_transformers import SentenceTransformer

from .base import EmbedderConfig


class CustomizedSentenceTransformer(SentenceTransformer):
    def embed_query(self, text: str) -> List[float]:
        return self.encode(sentences=[text])[0]

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return self.encode(sentences=texts)


class EmbedderLocal(EmbedderConfig):
    _pyclass: Type = CustomizedSentenceTransformer

    model_name_or_path: str = "BAAI/bge-base-en-v1.5"
