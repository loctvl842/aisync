import os
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, Type, TypeVar, Union


def get_project_root(
    start_path: Optional[Path] = None,
    root_marker: Union[str, List[str]] = ["pyproject.toml", "setup.py"],
) -> Optional[Path]:
    """
    Find the root directory of the project by looking for one or more specified marker files.

    Parameters:
        start_path (Optional[Path]): The directory to start searching from. Defaults to the directory containing this script.
        root_marker (Union[str, List[str]]): The filename or list of filenames that mark the root of the project
                                             (e.g., 'pyproject.toml' or ['pyproject.toml', 'setup.py']).

    Returns:
        Optional[Path]: The path to the project root directory, or None if not found.
    """
    start_path = Path(start_path or __file__).resolve()

    markers = [root_marker] if isinstance(root_marker, str) else root_marker
    for parent in [start_path, *start_path.parents]:
        if any((parent / marker).exists() for marker in markers):
            return parent
    return None


def get_registry_dir() -> str:
    """
    Returns the path to the registry directory.
    """
    home_dir = os.path.expanduser("~")
    return os.path.join(home_dir, ".aisync")


def get_suit_name(path_to_suit: str) -> str:
    """
    Returns the name of the suit.
    """
    path = Path(path_to_suit)
    return path.name if path.is_dir() else path.stem


# Design Patterns

T = TypeVar("T")


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


def memoize(func: Callable[..., T]) -> Callable[..., T]:
    """
    A decorator that caches the results of the function so future calls with
    the same arguments will return cached results.

    Example:
        @memoize
        def fibonacci(n: int) -> int:
            if n <= 1:
                return n
            return fibonacci(n - 1) + fibonacci(n - 2)
    """
    cache: Dict[Tuple[Any, ...], T] = {}

    def wrapper(*args, **kwargs) -> T:
        key = (args, tuple(kwargs.items()))
        if key not in cache:
            cache[key] = func(*args, **kwargs)
        return cache[key]

    return wrapper
