import asyncio
from typing import List, Optional

from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnableSequence

from . import prompts


class ChatChain:
    def __init__(self, suit, assistant):
        self._suit = suit
        self._chain = self._make_chain(assistant)

    def _format_input(self, assistant):
        return {
            "input": assistant.buffer_memory.get_pending_message(),
            "chat_history": assistant.buffer_memory.format_chat_history(),
        }

    def _make_prompt(
        self,
        prefix: str = prompts.DEFAULT_PROMPT_PREFIX,
        suffix: str = prompts.DEFAULT_PROMPT_SUFFIX,
        input_variables: Optional[List[str]] = None,
    ):
        template = "\n\n".join([prefix, suffix])
        if input_variables is None:
            input_variables = ["input", "chat_history"]
        return PromptTemplate(
            template=template,
            input_variables=input_variables,
        )

    def _make_chain(self, assistant) -> RunnableSequence:
        # Prepare prompt
        prompt_prefix = self._suit.execute_hook(
            "build_prompt_prefix", default=prompts.DEFAULT_PROMPT_PREFIX, assistant=assistant
        )
        prompt_suffix = self._suit.execute_hook(
            "build_prompt_suffix", default=prompts.DEFAULT_PROMPT_SUFFIX, assistant=assistant
        )
        prompt = self._make_prompt(prefix=prompt_prefix, suffix=prompt_suffix)
        chain = prompt | assistant.llm
        return chain

    def execute(self, assistant):
        input = self._format_input(assistant)

        if "tool_output" not in input:
            input["tool_output"] = ""

        res = {}
        res["output"] = self._chain.invoke(input, {"callbacks": assistant.callbacks})

        return res

    async def process_stream(self, assistant, queue: asyncio.Queue):
        input = self._format_input(assistant)

        if "tool_output" not in input:
            input["tool_output"] = ""

        async for chunk in self._chain.astream(input, assistant.config):
            chars = list(chunk.content)
            for c in chars:
                await queue.put(c)
