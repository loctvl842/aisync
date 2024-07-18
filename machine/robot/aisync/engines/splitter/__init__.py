import importlib
from typing import List, Optional

from .configs.base import SplitterConfig


def get_allowed_splitters() -> List[SplitterConfig]:
    default_allowed_splitters = []

    package_path = "machine.robot.aisync.engines.splitter.configs"

    module = importlib.import_module(package_path)
    for attr_name in dir(module):
        attr = getattr(module, attr_name)
        if hasattr(attr, "__bases__") and SplitterConfig in attr.__bases__:
            default_allowed_splitters.append(attr)

    # TODO: Allow using hook to custom allowed llms

    return default_allowed_splitters


def get_splitter_by_name(splitter_config_name: str) -> Optional[SplitterConfig]:
    splitters = get_allowed_splitters()
    for splitter in splitters:
        if splitter.__name__ == splitter_config_name:
            return splitter
    return None


def get_splitter_schemas():
    schemas = {}

    splitters = get_allowed_splitters()
    for cfg_cls in splitters:
        schemas[cfg_cls.__name__] = cfg_cls.model_json_schema()

    return schemas
