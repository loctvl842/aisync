from functools import wraps
from typing import Any, Callable, Optional, ParamSpec, TypeVar, Union, overload

from aisync.engines.graph import Node
from aisync.engines.graph.definitions import _Node

P = ParamSpec("P")
R = TypeVar("R")


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
