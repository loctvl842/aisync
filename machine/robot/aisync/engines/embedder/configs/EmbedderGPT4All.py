from typing import List, Type

from gpt4all import Embed4All

from .base import AscEmbedderConfig


class GP4ALLEmbedder(Embed4All):
    def __init__(self, model_name):
        super().__init__(model_name=model_name)

    def embed_query(self, text: str):
        return self.embed(text=text, dimensionality=768)

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed a list of documents using GPT4All.

        Args:
            texts: The list of texts to embed.

        Returns:
            List of embeddings, one for each text.
        """

        embeddings = [self.embed(text=text, dimensionality=768) for text in texts]
        return [list(map(float, e)) for e in embeddings]


class EmbedderGPT4All(AscEmbedderConfig):
    _pyclass: Type = GP4ALLEmbedder

    model_name: str = "nomic-embed-text-v1.5.f16.gguf"
