import importlib
from typing import List, Optional, Union

from .configs.base import AISyncLLM


def list_supported_llm_models() -> List[AISyncLLM]:
    """List all supported AISync LLMs from a package

    This function dynamically imports the module containing LLM configurations,
    identifies all classes that inherit from the base `AISyncLLM` class,
    and returns the list of subclasses.

    :return: A list of subclasses of `AISyncLLM` representing the supported LLMs in AISync.
    """
    supported_llms = []
    module = importlib.import_module(name=".configs", package=__package__)

    for attr_name in dir(module):
        attr = getattr(module, attr_name)
        if hasattr(attr, "__bases__") and AISyncLLM in attr.__bases__:
            supported_llms.append(attr)

    return supported_llms


def get_llm_cls(cls_name: str) -> Optional[AISyncLLM]:
    """Get AISyncLLM by its class name

    :param cls_name: The classname of AISyncLLM (e.g. "LLMChatOpenAI", …)
    :return: The corresponding AISyncLLM class if found; otherwise, `None`.
    """
    llms = list_supported_llm_models()
    for llm in llms:
        if llm.__name__ == cls_name:
            return llm
    return None


def get_llm_schemas():
    """Retrieve JSON schemas for all supported AISync LLM configurations.

    This function iterates over all language models supported by AISync,
    extracts their respective JSON schemas, and returns a dictionary
    where each key is the class name of the LLM, and the value is its schema.

    :return: A dictionary mapping the class names of supported AISync LLMs
             to their corresponding JSON schemas.
    """
    schemas = {}

    llms = list_supported_llm_models()
    for cfg_cls in llms:
        schemas[cfg_cls.__name__] = cfg_cls.model_json_schema()

    return schemas


def get_llm_object(llm_cls_name: Union[str, tuple[str, dict]]):
    """
    Get LLM object by its class name (e.g. "LLMChatOpenAI", …)

    :param llm_cls_name: Either a string representing the class name of the LLM (e.g., "LLMChatOpenAI")
                    or a tuple containing the class name and a configuration dictionary.
    :return: LLM object (e.g. ChatOpenAI, …)
    """
    llm_config = None
    if not isinstance(llm_cls_name, str):
        llm_cls_name, llm_config = llm_cls_name

    llm_cls = get_llm_cls(llm_cls_name)
    if llm_cls is None:
        raise ValueError(f"LLM {llm_cls_name} not found. Using LLMChatOpenAI instead.")

    llm_config = llm_config or llm_cls().model_dump()
    return llm_cls.get_llm(llm_config)
