import importlib
import os
from typing import List, Optional

from .configs.base import LLMConfig


def get_allowed_language_models() -> List[LLMConfig]:
    # TODO: Find better ways
    package_path = os.path.join("machine", "robot", "engines", "llm", "configs")
    init_by_path = os.path.join(package_path, "__init__.py")

    default_allowed_llms = []

    file_name = os.path.splitext(init_by_path)[0]
    module_name = file_name.replace(os.sep, ".")
    module = importlib.import_module(module_name)
    for attr_name in dir(module):
        attr = getattr(module, attr_name)
        if hasattr(attr, "__bases__") and LLMConfig in attr.__bases__:
            default_allowed_llms.append(attr)

    # TODO: Allow using hook to custom allowed llms

    return default_allowed_llms


def get_llm_by_name(llm_config_name: str) -> Optional[LLMConfig]:
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
