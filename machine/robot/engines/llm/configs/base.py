from typing import Type

from pydantic import BaseModel, ConfigDict


class LLMConfig(BaseModel):
    _pyclass: Type
    model_config = ConfigDict()

    @classmethod
    def get_llm(cls, config):
        return cls._pyclass.default(**config)
