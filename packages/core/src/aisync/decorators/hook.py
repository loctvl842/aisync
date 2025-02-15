import enum
from functools import wraps
from typing import Callable, Optional, ParamSpec, TypeVar, Union, overload

P = ParamSpec("P")
R = TypeVar("R")


class Hook:
    def __init__(self, call_fn: Callable[P, R]):
        self.call = call_fn
        self.name = call_fn.__name__

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} {self.name}>"

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> R:
        return self.call(*args, **kwargs)


class SupportedHook(str, enum.Enum):
    BEFORE_READ_MESSAGE = "before_read_message"
    BEFORE_SEND_MESSAGE = "before_send_message"
    SYSTEM_PROMPT = "build_system_prompt"
    SUIT_LLM = "set_suit_llm"


@overload
def hook(func: Callable[P, R]) -> Hook: ...


@overload
def hook(name: str) -> Callable[[Callable[P, R]], Hook]: ...


@overload
def hook(*, name: Optional[str] = None) -> Callable[[Callable[P, R]], Hook]: ...


def hook(
    func: Optional[Callable[P, R]] = None,
    *,
    name: Optional[str] = None,
) -> Union[Hook, Callable[[Callable[P, R]], Hook]]:
    """
    A decorator to convert a function into a Hook instance.

    Can be used in multiple ways:

    - @hook
    - @hook("custom_name")
    - @hook(name="custom_name")
    """
    if isinstance(func, str):
        name = func
        func = None

    def decorator(call_fn: Callable[P, R]) -> Hook:
        hook_instance = Hook(call_fn)
        hook_instance.name = name if name else call_fn.__name__
        wraps(call_fn)(hook_instance)  # Copy metadata
        return hook_instance

    if func is not None:
        # Called as @hook
        return decorator(func)

    # Called as @hook(...)
    return decorator
