from typing import Type

from langchain.text_splitter import CharacterTextSplitter

from .base import SplitterConfig


class SplitterCharacter(SplitterConfig):
    _pyclass: Type = CharacterTextSplitter

    chunk_size: int = 500
    chunk_overlap: int = 24
