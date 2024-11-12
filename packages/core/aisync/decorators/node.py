from functools import wraps
from typing import Any, Callable, Optional, ParamSpec, TypeVar, Union, get_type_hints, overload

P = ParamSpec("P")
R = TypeVar("R")


class Node:
    def __init__(self, name: str, call_fn: Callable[P, R], llm: Optional[Any] = None):
        self.call = call_fn
        self.llm = llm
        self.name = name

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} {self.name}>"

    @property
    def action(self) -> Callable[..., R]:
        """Wraps `self.call`, injects `llm` if available, and modifies type hints to exclude `llm`."""
        original_type_hints = get_type_hints(self.call)
        adjusted_type_hints = {k: v for k, v in original_type_hints.items() if k != "llm"}

        @wraps(self.call)
        def action(*args: P.args, **kwargs: P.kwargs) -> R:
            if self.llm is not None:
                kwargs["llm"] = self.llm
            return self.call(*args, **kwargs)

        action.__annotations__ = adjusted_type_hints
        return action

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> R:
        return self.action(*args, **kwargs)


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

        node_instance = Node(node_name, call_fn, llm=llm)

        # Use @wraps to copy metadata from call_fn to node_instance
        wraps(call_fn)(node_instance)
        return node_instance

    if func is not None:
        # Then, called as @node
        return decorator(func)

    # called as @node(...)
    return decorator
