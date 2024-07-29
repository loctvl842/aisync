import importlib
from typing import List, Optional, Union

from .configs.base import RerankerConfig


def get_allowed_rerankers() -> List[RerankerConfig]:
    default_allowed_rerankers = []

    package_path = "machine.robot.aisync.engines.reranker.configs"

    module = importlib.import_module(package_path)
    for attr_name in dir(module):
        attr = getattr(module, attr_name)
        if hasattr(attr, "__bases__") and RerankerConfig in attr.__bases__:
            default_allowed_rerankers.append(attr)

    # TODO: Allow using hook to custom allowed rerankers

    return default_allowed_rerankers


def get_reranker_by_name(reranker_config_name: str) -> Optional[RerankerConfig]:
    rerankers = get_allowed_rerankers()
    for reranker in rerankers:
        if reranker.__name__ == reranker_config_name:
            return reranker
    return None


def get_reranker_schemas():
    schemas = {}

    rerankers = get_allowed_rerankers()
    for cfg_cls in rerankers:
        schemas[cfg_cls.__name__] = cfg_cls.model_json_schema()

    return schemas


def get_reranker_object(reranker_config: Union[str, tuple[str, dict]], **kwargs):
    reranker_name, reranker_schema = None, None

    if isinstance(reranker_config, str):
        reranker_name = reranker_config
    elif isinstance(reranker_config, tuple):
        reranker_name, reranker_schema = reranker_config

    cfg_cls = get_reranker_by_name(reranker_name)
    if cfg_cls is None:
        raise ValueError(f"Reranker {reranker_name} not found. Using RerankerCrossEncoder instead.")

    if reranker_schema is None:
        reranker_schema = cfg_cls().model_dump()
    return cfg_cls.get_reranker(reranker_schema)
