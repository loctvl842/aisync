from typing import Type

from pydantic import BaseModel, ConfigDict


class AISyncLLM(BaseModel):
    _pyclass: Type
    model_config = ConfigDict(protected_namespaces=())

    @classmethod
    def get_llm(cls, config) -> Type:
        return cls._pyclass.default(**config)
