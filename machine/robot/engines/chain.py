from typing import List, Optional

from langchain.chains.llm import LLMChain
from langchain_core.prompts import PromptTemplate

from machine.robot.engines import prompts


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

    def _make_chain(self, assistant):
        # Prepare prompt
        prompt_prefix = self._suit.execute_hook(
            "build_prompt_prefix", default=prompts.DEFAULT_PROMPT_PREFIX, assistant=assistant
        )
        prompt_suffix = self._suit.execute_hook(
            "build_prompt_suffix", default=prompts.DEFAULT_PROMPT_SUFFIX, assistant=assistant
        )
        prompt = self._make_prompt(prefix=prompt_prefix, suffix=prompt_suffix)
        # TODO: Verbose if dev environment only
        return LLMChain(prompt=prompt, llm=assistant.llm, verbose=True)

    def execute(self, assistant):
        input = self._format_input(assistant)

        if "tool_output" not in input:
            input["tool_output"] = ""

        res = self._chain.invoke(input)
        res["output"] = res["text"]
        del res["text"]
        return res
