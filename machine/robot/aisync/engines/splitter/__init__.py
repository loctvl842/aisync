import importlib
from typing import List, Optional, Union

import core.utils as ut

from .configs.base import AISyncSplitter


def list_supported_splitter_models() -> List[AISyncSplitter]:
    """List of all supported AISync splitters from a package

    This function dynamically imports the module containing splitter configurations,
    identifies all classes that inherit from the base `AISyncSplitter` class,
    and returns them as a list of supported splitters.

    :return: A list of classes representing the supported splitters in AISync.
    """
    supported_splitters = []
    module = importlib.import_module(name=".configs", package=__package__)

    for attr_name in dir(module):
        attr = getattr(module, attr_name)
        if hasattr(attr, "__bases__") and AISyncSplitter in attr.__bases__:
            supported_splitters.append(attr)

    return supported_splitters


def get_splitter_cls(cls_name: str) -> Optional[AISyncSplitter]:
    """Get AISyncSplitter by its class name

    :param cls_name: The classname of AISyncSplitter(e.g. "SplitterCharacter", …)
    :return: The corresponding AISyncSplitter class if found; otherwise, `None`.
    """
    splitters = list_supported_splitter_models()
    for splitter in splitters:
        if splitter.__name__ == cls_name:
            return splitter
    return None


def get_splitter_schemas():
    """Retrieve JSON schemas for all supported AISync Splitter configurations.

    This function iterates over all language models supported by AISync,
    extracts their respective JSON schemas, and returns a dictionary
    where each key is the class name of the Splitter, and the value is its schema.

    :return: A dictionary mapping the class names of supported AISync Splitters
             to their corresponding JSON schemas.
    """
    schemas = {}

    splitters = list_supported_splitter_models()
    for cfg_cls in splitters:
        schemas[cfg_cls.__name__] = cfg_cls.model_json_schema()

    return schemas


def get_splitter_object(splitter_cls_name: Union[str, tuple[str, dict]], **kwargs):
    """
    Get Splitter object by its class name (e.g. "SplitterCharacter",…)

    :param splitter_cls_name: Either a string representing the class name of the Splitter (e.g., "SplitterCharacter")
                    or a tuple containing the class name and a configuration dictionary.
    :return: Splitter object (e.g. SplitterCharacter, …)
    """
    splitter_config = None
    if not isinstance(splitter_cls_name, str):
        splitter_cls_name, splitter_config = splitter_cls_name

    splitter_cls = get_splitter_cls(splitter_cls_name)
    if splitter_cls is None:
        raise ValueError(f"Splitter {splitter_cls_name} not found. Using SplitterCharacter instead.")

    splitter_config = ut.dict_deep_extend(splitter_cls().model_dump(), splitter_config or {})
    splitter_obj = splitter_cls.get_splitter(splitter_config)

    if splitter_cls_name == "SplitterSemantic":
        embedder = kwargs.get("embedder", None)
        if embedder is None:
            raise ValueError("Embedder is required for SplitterSemantic")
        splitter_obj.set_embedder(embedder)

    return splitter_obj
