from typing import Type

from pydantic import BaseModel, ConfigDict


class AISyncEmbedder(BaseModel):
    _pyclass: Type
    model_config = ConfigDict(protected_namespaces=())

    @classmethod
    def get_embedder(cls, config):
        return cls._pyclass.default(**config)
