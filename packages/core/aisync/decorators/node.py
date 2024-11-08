from functools import wraps
from typing import Callable, Optional, ParamSpec, TypeVar, get_type_hints

from langchain_core.runnables import Runnable

P = ParamSpec("P")
R = TypeVar("R")


class Node:
    def __init__(self, name: str, call_fn: Callable[P, R], llm: Optional[Runnable] = None):
        self.call = call_fn
        self.llm = llm
        self.name = name

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} {self.name}>"

    @property
    def action(self) -> Callable[..., R]:
        """Wraps `self.call`, injects `llm` if available, and modifies type hints to exclude `llm`."""

        # Get the original type hints for `node.call`
        original_type_hints = get_type_hints(self.call)

        # Create a copy of the type hints without `llm`
        adjusted_type_hints = {k: v for k, v in original_type_hints.items() if k != "llm"}

        @wraps(self.call)
        def action(*args: P.args, **kwargs: P.kwargs) -> R:
            # Inject `llm` into kwargs if available
            if self.llm is not None:
                kwargs["llm"] = self.llm
            return self.call(*args, **kwargs)

        # Apply the adjusted type hints to `action`, omitting `llm`
        action.__annotations__ = adjusted_type_hints

        return action


def node(*args, name: Optional[str] = None, llm: Optional[Runnable] = None):
    def _make_with_name(node_name: str) -> Callable:
        def _make_node(call_fn: Callable) -> Node:
            node_ = Node(node_name, call_fn, llm=llm)
            return node_

        return _make_node

    if len(args) == 1 and isinstance(args[0], str):
        # Then, called as @node("name")
        return _make_with_name(args[0])
    elif len(args) == 1 and callable(args[0]):
        # Then, called as @node
        func = args[0]
        node_name = name if name else func.__name__
        return _make_with_name(node_name)(func)
    elif len(args) == 0 and name:
        # Then, called as @node(name="name")
        return _make_with_name(name)
    elif len(args) == 0:
        # called as @node(*args, **kwargs)
        def _decorator(call_fn):
            return _make_with_name(call_fn.__name__)(call_fn)

        return _decorator
    else:
        raise ValueError("Invalid usage of @node")
