from .node import Node
from typing import Optional, List
from .prompts import FORMAT_INSTRUCTIONS, ActionPromptTemplate, DOC_PROMPT, DEFAULT_AGENT_PROMPT_SUFFIX, DEFAULT_PROMPT_SUFFIX, DEFAULT_PROMPT_PREFIX


class NodeCore(Node):
    def __init__(
        self,
        name: str,
        prompt_prefix: Optional[str]=DEFAULT_PROMPT_PREFIX,
        prompt_suffix: Optional[str]=DEFAULT_PROMPT_SUFFIX,
        conditional_prompt: Optional[str]="",
        tools: Optional[List[str]]=[],
        document_names: Optional[List[str]]=[],
        interrupt_before: Optional[List[str]]=[],
        next_nodes: Optional[List[str]]=[]
    ):
        super().__init__(
            name, 
            prompt_prefix, 
            prompt_suffix,
            conditional_prompt,
            tools,
            document_names,
            interrupt_before,
            next_nodes
        )
    async def setup_input(self, state):
        """
        Override the setup_input of node to include persist-memory
        """
        input = await super().setup_input(state)
        input["persist_memory"] = await self.persist_memory()
        return input
    