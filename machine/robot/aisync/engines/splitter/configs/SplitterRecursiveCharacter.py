from typing import Type

from langchain.text_splitter import RecursiveCharacterTextSplitter

from .base import AisyncSplitter


class SplitterRecursiveCharacter(AisyncSplitter):
    _pyclass: Type = RecursiveCharacterTextSplitter

    chunk_size: int = 500
    chunk_overlap: int = 24
