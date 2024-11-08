from typing import Type, TypedDict

from pydantic import BaseModel


class State:
    _instance = None
    _current_state_schema = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(State, cls).__new__(cls)
        return cls._instance

    def set_schema(self, schema: Type):
        self._current_state_schema = schema

    def get_schema(self):
        return self._current_state_schema

def state(cls: Type):
    """Decorator to register a class as State schema
    """

    if not issubclass(cls, (TypedDict, BaseModel)):
        raise TypeError(f"@state can only be applied to TypedDict or BaseModel, not {type(cls).__name__}")

    cls.set_schema(cls)

    return cls
