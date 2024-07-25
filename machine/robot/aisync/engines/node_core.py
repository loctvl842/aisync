from typing import TYPE_CHECKING, List, Optional

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
    ):
        super().__init__(
            name, prompt_prefix, prompt_suffix, conditional_prompt, tools, document_names, interrupt_before, next_nodes
        )

    async def setup_input(self, state: "State") -> dict:
        """
        Override the setup_input of node to include persist-memory
        """
        await super().setup_input(state)
        self.input["persist_memory"] = await self.persist_memory()
