from typing import Type

from langchain.text_splitter import CharacterTextSplitter

from .base import AISyncSplitter


class SplitterCharacter(AISyncSplitter):
    _pyclass: Type = CharacterTextSplitter

    chunk_size: int = 500
    chunk_overlap: int = 24
