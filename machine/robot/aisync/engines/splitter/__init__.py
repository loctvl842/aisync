import importlib
from typing import List, Optional, Union

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


def get_splitter_object(splitter_config: Union[str, tuple[str, dict]], **kwargs):
    embedder = kwargs.get("embedder", None)
    splitter_name, splitter_schema = None, None

    current_splitter = None

    if isinstance(splitter_config, str):
        splitter_name = splitter_config
    elif isinstance(splitter_config, tuple):
        splitter_name, splitter_schema = splitter_config

    cfg_cls = get_splitter_by_name(splitter_name)
    if cfg_cls is None:
        raise ValueError(f"Splitter {splitter_name} not found. Using SplitterCharacter instead.")

    if splitter_schema is None:
        splitter_schema = cfg_cls().model_dump()
    current_splitter = cfg_cls.get_splitter(splitter_schema)
    if splitter_name == "SplitterSemantic":
        if embedder is None:
            raise ValueError("Embedder is required for SplitterSemantic")
        current_splitter.set_embedder(embedder)

    return current_splitter
