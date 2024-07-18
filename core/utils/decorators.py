import asyncio
import time
from functools import wraps
from typing import Awaitable, Callable, TypeVar, Union

T = TypeVar("T")


def singleton(cls):
    """
    A decorator function that ensures a class has only one instance and provides a global point of access to it.
    """

    instances = {}

    def wrapper(*args, **kwargs):
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]

    return wrapper


def stopwatch(
    prefix: str = "",
) -> Callable[[Callable[..., T]], Callable[..., Union[T, Awaitable[T]]]]:
    """
    A decorator function that measures the time taken by a function to execute.

    Usage:
        @stopwatch(prefix="prefix")
        async def my_function():
            pass
    """

    def decorator(fn: Callable[..., T]) -> Callable[..., Union[T, Awaitable[T]]]:
        @wraps(fn)
        def wrapper(*args, **kwargs) -> Union[T, Awaitable[T]]:
            from core.logger import syslog

            start = time.time_ns()

            def do(elapsed_time):
                syslog.info(f"Elapsed time for {''.join([prefix + ':' if prefix else '', fn.__name__])}: {elapsed_time} ms")

            if asyncio.iscoroutinefunction(fn):

                async def async_wrapper() -> T:
                    result = await fn(*args, **kwargs)
                    end = time.time_ns()
                    elapsed_time = (end - start) / 1e6
                    do(elapsed_time)
                    return result

                return async_wrapper()
            else:
                result = fn(*args, **kwargs)
                end = time.time_ns()
                elapsed_time = (end - start) / 1e6
                do(elapsed_time)
                return result

        return wrapper

    return decorator
