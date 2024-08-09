import importlib
from typing import List, Optional, Union

from .configs.base import AisyncLLM


def get_allowed_language_models() -> List[AisyncLLM]:
    default_allowed_llms = []

    package_path = "machine.robot.aisync.engines.llm.configs"

    module = importlib.import_module(package_path)
    for attr_name in dir(module):
        attr = getattr(module, attr_name)
        if hasattr(attr, "__bases__") and AisyncLLM in attr.__bases__:
            default_allowed_llms.append(attr)

    # TODO: Allow using hook to custom allowed llms

    return default_allowed_llms


def get_asc_llm_by_name(llm_config_name: str) -> Optional[AisyncLLM]:
    llms = get_allowed_language_models()
    for llm in llms:
        if llm.__name__ == llm_config_name:
            return llm
    return None


def get_llm_schemas():
    schemas = {}

    llms = get_allowed_language_models()
    for cfg_cls in llms:
        schemas[cfg_cls.__name__] = cfg_cls.model_json_schema()

    return schemas


def get_llm_object(llm_config: Union[str, tuple[str, dict]], **kwargs):
    llm_name, llm_schema = None, None
    if isinstance(llm_config, str):
        llm_name = llm_config
    elif isinstance(llm_config, tuple):
        llm_name, llm_schema = llm_config

    cfg_cls = get_asc_llm_by_name(llm_name)
    if cfg_cls is None:
        raise ValueError(f"LLM {llm_name} not found. Using AscLLMChatOpenAI instead.")
    if llm_schema is None:
        llm_schema = cfg_cls().model_dump()

    return cfg_cls.get_llm(llm_schema)
