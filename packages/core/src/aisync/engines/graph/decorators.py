from functools import wraps
from typing import Any, Callable, Optional, ParamSpec, TypeVar, Union, overload

from .base import Node, Hook
from .definitions import _Node


P = ParamSpec("P")
R = TypeVar("R")


"""
# Nodes
"""


@overload
def node(func: Callable[P, R]) -> Node: ...


@overload
def node(name: str, *, llm: Optional[Any] = None) -> Callable[[Callable[P, R]], Node]: ...


@overload
def node(*, name: Optional[str] = None, llm: Optional[Any] = None) -> Callable[[Callable[P, R]], Node]: ...


def node(
    func: Optional[Callable[P, R]] = None,
    *,
    name: Optional[str] = None,
    llm: Optional[Any] = None,
) -> Union[Node, Callable[[Callable[P, R]], Node]]:
    """
    A decorator to convert a function into a Node instance.

    Can be used in multiple ways:

    - @node
    - @node("custom_name")
    - @node(name="custom_name")
    - @node(name="custom_name", llm=custom_llm)
    """
    if isinstance(func, str):
        name = func
        func = None

    def decorator(call_fn: Callable[P, R]) -> Node:
        node_name = name if name else call_fn.__name__

        node_instance = _Node(node_name, call_fn, llm=llm)

        # Use @wraps to copy metadata from call_fn to node_instance
        wraps(call_fn)(node_instance)
        return node_instance

    if func is not None:
        # Then, called as @node
        return decorator(func)

    # called as @node(...)
    return decorator


"""
# Hooks
"""


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
