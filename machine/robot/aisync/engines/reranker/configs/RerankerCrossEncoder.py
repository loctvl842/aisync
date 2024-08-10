from typing import Type

from sentence_transformers import CrossEncoder

from .base import AISyncReranker


class RerankerCrossEncoder(AISyncReranker):
    _pyclass: Type = CrossEncoder

    model_name: str = "cross-encoder/ms-marco-MiniLM-L-2-v2"
    num_labels: int = 1
