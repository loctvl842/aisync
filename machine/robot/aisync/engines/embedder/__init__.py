import importlib
from typing import List, Optional, Union

from .configs.base import AISyncEmbedder


def list_supported_embedder_models() -> List[AISyncEmbedder]:
    """List of all supported AISync embedders from a package

    This function dynamically imports the module containing embedder configurations,
    identifies all classes that inherit from the base `AISyncEmbedder` class,
    and returns them as a list of supported embedders.

    :return: A list of classes representing the supported embedders in AISync.
    """
    supported_embedders = []
    module = importlib.import_module(name=".configs", package=__package__)

    for attr_name in dir(module):
        attr = getattr(module, attr_name)
        if hasattr(attr, "__bases__") and AISyncEmbedder in attr.__bases__:
            supported_embedders.append(attr)

    return supported_embedders


def get_embedder_cls(cls_name: str) -> Optional[AISyncEmbedder]:
    """Get an AISync embedder class by its name.

    :param cls_name: The name of the embedder class (e.g., "EmbedderOpenAI").
    :return: The corresponding AISyncEmbedder class if found; otherwise, `None`.
    """
    embedders = list_supported_embedder_models()
    for embedder in embedders:
        if embedder.__name__ == cls_name:
            return embedder
    return None


def get_embedder_schemas():
    """Retrieve JSON schemas for all supported AISync Embedder configurations.

    This function iterates over all embedder models supported by AISync,
    extracts their respective JSON schemas, and returns a dictionary
    where each key is the class name of the Embedder, and the value is its schema.

    :return: A dictionary mapping the class names of supported AISync Embedders
             to their corresponding JSON schemas.
    """
    schemas = {}

    embedders = list_supported_embedder_models()
    for cfg_cls in embedders:
        schemas[cfg_cls.__name__] = cfg_cls.model_json_schema()

    return schemas


def get_embedder_object(embedder_cls_name: Union[str, tuple[str, dict]]):
    """
    Get Embedder object by its class name (e.g. "EmbedderOpenAI",…)

    :param embedder_cls_name: Either a string representing the class name of the Embedder (e.g., "EmbedderOpenAI")
                    or a tuple containing the class name and a configuration dictionary.
    :return: Embedder object (e.g. EmbedderOpenAI, …)
    """
    embedder_config = None
    if not isinstance(embedder_cls_name, str):
        embedder_cls_name, embedder_config = embedder_cls_name

    embedder_cls = get_embedder_cls(embedder_cls_name)
    if embedder_cls is None:
        raise ValueError(f"Embedder {embedder_cls_name} not found. Using EmbedderOpenAI instead.")

    embedder_config = embedder_config or embedder_cls().model_dump()
    return embedder_cls.get_embedder(embedder_config)
