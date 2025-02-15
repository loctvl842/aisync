from functools import wraps
from typing import Any, Callable, Dict, Tuple, Type, TypeVar

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
