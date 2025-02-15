import importlib
from typing import List, Optional, Type, Union

from aisync.utils import dict_deep_extend
from pydantic import BaseModel, ConfigDict


class AISyncLLM(BaseModel):
    """Base class for AISync language models.

    This class provides the structure for configuring and retrieving
    language model instances within the AISync framework.

    Attributes:
        _pyclass (Type): A class reference to the default language model implementation.
        model_config (ConfigDict): Configuration options specific to the AISync model.
    """

    _pyclass: Type
    model_config = ConfigDict(protected_namespaces=())

    @classmethod
    def get_llm(cls, config) -> Type:
        """Retrieve an LLM instance based on configuration.

        Args:
            config (dict): Configuration parameters for initializing the LLM.

        Returns:
            Type: An instance of the LLM configured with the provided parameters.
        """
        return cls._pyclass.default(**config)


def list_supported_llm_models() -> List[AISyncLLM]:
    """Lists all supported AISync LLM classes from the configuration module.

    Dynamically imports the module containing LLM configurations, identifies
    all classes inheriting from the base `AISyncLLM` class, and returns them.

    Returns:
        List[AISyncLLM]: A list of subclasses of `AISyncLLM` representing supported LLMs.
    """
    supported_llms = []
    module = importlib.import_module(name=".configs", package=__package__)

    for attr_name in dir(module):
        attr = getattr(module, attr_name)
        if hasattr(attr, "__bases__") and AISyncLLM in attr.__bases__:
            supported_llms.append(attr)

    return supported_llms


def get_llm_cls(cls_name: str) -> Optional[AISyncLLM]:
    """Retrieve an AISyncLLM class by its name.

    Args:
        cls_name (str): The name of the AISyncLLM subclass (e.g., "LLMChatOpenAI").

    Returns:
        Optional[AISyncLLM]: The corresponding AISyncLLM class if found; otherwise, None.
    """
    llms = list_supported_llm_models()
    for llm in llms:
        if llm.__name__ == cls_name:
            return llm
    return None


def get_llm_schemas():
    """Retrieve JSON schemas for all supported AISync LLM configurations.

    Iterates over all language models supported by AISync, extracting
    their respective JSON schemas, and returns a dictionary mapping
    class names to schemas.

    Returns:
        dict: A dictionary where keys are class names of supported AISync LLMs
              and values are their corresponding JSON schemas.
    """
    schemas = {}

    llms = list_supported_llm_models()
    for cfg_cls in llms:
        schemas[cfg_cls.__name__] = cfg_cls.model_json_schema()

    return schemas


def get_llm_object(llm_cls_name: Union[str, tuple[str, dict]]):
    """Get an LLM object instance by its class name or class/configuration tuple.

    Args:
        llm_cls_name (Union[str, tuple[str, dict]]): Either a string representing
            the class name of the LLM (e.g., "LLMChatOpenAI") or a tuple containing
            the class name and a configuration dictionary.

    Returns:
        Any: An instance of the specified LLM class, configured with provided parameters.

    Raises:
        ValueError: If the specified LLM class name is not found in the AISync LLMs.
    """
    llm_config = None
    if not isinstance(llm_cls_name, str):
        llm_cls_name, llm_config = llm_cls_name

    llm_cls = get_llm_cls(llm_cls_name)
    if llm_cls is None:
        raise ValueError(f"LLM {llm_cls_name} not found. Using LLMChatOpenAI instead.")

    llm_config = dict_deep_extend(llm_cls().model_dump(), llm_config or {})
    return llm_cls.get_llm(llm_config)
