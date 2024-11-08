import os
from functools import reduce, wraps
from typing import Any, Callable, Mapping, Type, TypeVar

T = TypeVar("T")


def dict_deep_extend(*dicts: dict[Any, Any]) -> dict[Any, Any]:
    """
    Deeply merge multiple dictionaries.
    Later dictionaries take precedence over earlier ones.

    Args:
        *dicts: An arbitrary number of dictionaries to merge.

    Returns:
        A new dictionary resulting from deep merging the input dictionaries.

    Raises:
        TypeError: If any of the arguments is not a dictionary.
    """

    def merge(a: dict[Any, Any], b: dict[Any, Any]) -> dict[Any, Any]:
        """
        Recursively merge dictionary b into dictionary a.

        Args:
            a: The base dictionary.
            b: The dictionary to merge into a.

        Returns:
            The merged dictionary.
        """
        for key, b_value in b.items():
            if key in a:
                a_value = a[key]
                if isinstance(a_value, Mapping) and isinstance(b_value, Mapping):
                    a[key] = merge(a_value.copy(), b_value)
                else:
                    a[key] = b_value
            else:
                a[key] = b_value
        return a

    if not dicts:
        return {}

    # Validate all inputs are dictionaries
    for idx, d in enumerate(dicts, start=1):
        if not isinstance(d, Mapping):
            raise TypeError(f"Argument {idx} is not a dictionary: {d!r}")

    return reduce(merge, dicts, {})


def singleton(cls: Type[T]) -> Callable[..., T]:
    """
    A decorator function that ensures a class has only one instance and provides a global point of access to it.

    Returns:
        Callable[..., T]: The singleton instance of the class.
    """

    instances = {}

    @wraps(cls)
    def wrapper(*args, **kwargs):
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]

    return wrapper


def get_suits_path() -> str:
    """
    Returns the path to the plugins folder.
    """

    return os.path.join("core", "robot", "suits")


def get_suit_name(path_to_suit: str) -> str:
    """
    Returns the name of the suit.
    """
    return os.path.basename(path_to_suit)
