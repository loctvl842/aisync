import importlib
from typing import List, Optional

from .configs.base import EmbedderConfig


def get_allowed_embedder_models() -> List[EmbedderConfig]:
    default_allowed_embedders = []
    package_path = "machine.robot.aisync.engines.embedder.configs"

    module = importlib.import_module(package_path)
    for attr_name in dir(module):
        attr = getattr(module, attr_name)
        if hasattr(attr, "__bases__") and EmbedderConfig in attr.__bases__:
            default_allowed_embedders.append(attr)

    # TODO: Allow using hook to custom allowed llms

    return default_allowed_embedders


def get_embedder_by_name(embedder_config_name: str) -> Optional[EmbedderConfig]:
    embedders = get_allowed_embedder_models()
    for embedder in embedders:
        if embedder.__name__ == embedder_config_name:
            return embedder
    return None


def get_embedder_schemas():
    schemas = {}

    embedders = get_allowed_embedder_models()
    for cfg_cls in embedders:
        schemas[cfg_cls.__name__] = cfg_cls.model_json_schema()

    return schemas
