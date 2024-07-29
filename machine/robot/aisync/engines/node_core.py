from typing import TYPE_CHECKING, List, Literal, Optional

from .node import Node
from .prompts import (
    DEFAULT_PROMPT_PREFIX,
    DEFAULT_PROMPT_SUFFIX,
)

if TYPE_CHECKING:
    from .compiler import State


class NodeCore(Node):
    def __init__(
        self,
        name: str,
        prompt_prefix: Optional[str] = DEFAULT_PROMPT_PREFIX,
        prompt_suffix: Optional[str] = DEFAULT_PROMPT_SUFFIX,
        conditional_prompt: Optional[str] = "",
        tools: Optional[List[str]] = [],
        document_names: Optional[List[str]] = [],
        interrupt_before: Optional[List[str]] = [],
        next_nodes: Optional[List[str]] = [],
        execution_components: Optional[List[Literal["tool", "persist_memory", "document_memory"]]] = [
            "tool",
            "persist_memory",
            "document_memory",
        ],
    ):
        super().__init__(
            name=name,
            prompt_prefix=prompt_prefix,
            prompt_suffix=prompt_suffix,
            conditional_prompt=conditional_prompt,
            tools=tools,
            document_names=document_names,
            interrupt_before=interrupt_before,
            next_nodes=next_nodes,
            execution_components=execution_components,
        )
