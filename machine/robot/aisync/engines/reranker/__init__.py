import importlib
from typing import List, Optional, Union

import core.utils as ut

from .configs.base import AISyncReranker


def list_supported_reranker_models() -> List[AISyncReranker]:
    """List of all supported AISync rerankers from a package

    This function dynamically imports the module containing reranker configurations,
    identifies all classes that inherit from the base `AISyncReranker` class,
    and returns them as a list of supported rerankers.

    :return: A list of classes representing the supported rerankers in AISync.
    """
    default_allowed_rerankers = []
    module = importlib.import_module(name=".configs", package=__package__)

    for attr_name in dir(module):
        attr = getattr(module, attr_name)
        if hasattr(attr, "__bases__") and AISyncReranker in attr.__bases__:
            default_allowed_rerankers.append(attr)

    return default_allowed_rerankers


def get_reranker_cls(cls_name: str) -> Optional[AISyncReranker]:
    """Get an AISync reranker class from its name

    :param cls_name: The name of reranker class (e.g. "RerankerCrossEncoder")
    :return: The corresponding AISyncReranker class if found; otherwise, `None`.
    """
    rerankers = list_supported_reranker_models()
    for reranker in rerankers:
        if reranker.__name__ == cls_name:
            return reranker
    return None


def get_reranker_schemas():
    """Retrieve JSON schemas for all supported AISync Reranker configurations.

    This function iterates over all reranker models supported by AISync,
    extracts their respective JSON schemas, and returns a dictionary
    where each key is the class name of the Reranker, and the value is its schema.

    :return: A dictionary mapping the class names of supported AISync Rerankers
             to their corresponding JSON schemas.
    """
    schemas = {}

    rerankers = list_supported_reranker_models()
    for cfg_cls in rerankers:
        schemas[cfg_cls.__name__] = cfg_cls.model_json_schema()

    return schemas


def get_reranker_object(reranker_cls_name: Union[str, tuple[str, dict]]):
    """
    Get Reranker object by its class name (e.g. "RerankerCrossEncoder",…)

    :param reranker_cls_name: Either a string representing the class name of the Reranker (e.g., "RerankerCrossEncoder")
                    or a tuple containing the class name and a configuration dictionary.
    :return: Reranker object (e.g. RerankerCrossEncoder, …)
    """
    reranker_config = None
    if not isinstance(reranker_cls_name, str):
        reranker_cls_name, reranker_config = reranker_cls_name

    reranker_cls = get_reranker_cls(reranker_cls_name)
    if reranker_cls is None:
        raise ValueError(f"Reranker {reranker_cls_name} not found. Using RerankerCrossEncoder instead.")

    reranker_config = ut.dict_deep_extend(reranker_cls().model_dump(), reranker_config)
    return reranker_cls.get_reranker(reranker_config)
