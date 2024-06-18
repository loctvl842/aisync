from typing import Type

from gpt4all import Embed4All

from .base import EmbedderConfig


class GP4ALLEmbedder(Embed4All):
    def __init__(self, model_name):
        super().__init__(model_name=model_name)

    def embed_query(self, text: str):
        return self.embed(text=text, dimensionality=768)


class EmbedderGPT4All(EmbedderConfig):
    _pyclass: Type = GP4ALLEmbedder

    model_name: str = "nomic-embed-text-v1.5.f16.gguf"
