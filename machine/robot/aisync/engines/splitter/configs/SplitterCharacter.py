from typing import Type

from langchain.text_splitter import CharacterTextSplitter

from .base import AisyncSplitter


class SplitterCharacter(AisyncSplitter):
    _pyclass: Type = CharacterTextSplitter

    chunk_size: int = 500
    chunk_overlap: int = 24
