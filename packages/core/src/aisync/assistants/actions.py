import importlib
from typing import List, Tuple, Type

from aisync.assistants.base import Assistant


def get_assistants() -> List[Tuple[str, Type[Assistant]]]:
    options = []
    package_path = "aisync.assistants"

    try:
        module = importlib.import_module(package_path)
    except ImportError:
        raise ImportError(f"Could not import module {package_path}")
    for attr_name in dir(module):
        attr = getattr(module, attr_name)
        if hasattr(attr, "__bases__") and Assistant in attr.__bases__:
            class_name = attr.__name__
            ai_class = attr
            options.append((class_name, ai_class))
    return options


def get_assistant(name: str) -> Type[Assistant]:
    for class_name, ai_class in get_assistants():
        if class_name == name:
            return ai_class
