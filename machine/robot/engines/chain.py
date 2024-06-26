import traceback
from typing import Callable, List, Optional

from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnableSequence

from core.logger import syslog

from ..assistants.base.assistant import Assistant
from . import prompts


class ChatChain:
    def __init__(self, suit, assistant):
        self._suit = suit
        self._chain = self._make_chain(assistant)

    def _format_input(self, assistant: Assistant):
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

    async def invoke(self, assistant: Assistant):
        input = self._format_input(assistant)

        # Get tools from all chatbot suits
        tools = list(self._suit.tools.values())

        if len(tools) > 0:
            try:
                res = assistant.agent_manager.execute_tools(agent_input=input, tools=tools, assistant=assistant)
                if res is None:
                    input["tool_output"] = ""
                else:
                    tool_output = res["output"]
                    input["tool_output"] = f"## Tool Output: `{tool_output}`" if tool_output else ""

            except Exception as e:
                syslog.error(f"Error when executing tools: {e}")
                traceback.print_exc()

        if "tool_output" not in input:
            input["tool_output"] = ""

        # Embed input
        self.vectorized_input = self._suit.execute_hook("embed_input", input=input["input"], assistant=assistant)

        lt_memory = await assistant.persist_memory.similarity_search(vectorized_input=self.vectorized_input)
        input["persist_memory"] = lt_memory["persist_memory"]

        # fetch document_memory
        try:
            doc = await assistant.document_memory.similarity_search(vectorized_input=self.vectorized_input)
            document_memory = assistant.agent_manager.execute_documents(
                agent_input={"input": input["input"], "document": doc}, assistant=assistant
            )
            input["document_memory"] = f"## Document Knowledge Output: `{document_memory}`"
        except Exception as e:
            syslog.error(f"Error when fetching document memory: {e}")
            traceback.print_exc()

        if "document_memory" not in input:
            input["document_memory"] = ""

        res = {}
        ai_response = self._chain.invoke(input, config=assistant.config)
        if isinstance(ai_response, str):
            res["output"] = ai_response
        else:
            res["output"] = ai_response.content

        return res

    async def stream(self, assistant, handle_chunk: Callable):
        input = self._format_input(assistant)

        # Get tools from all chatbot suits
        tools = list(self._suit.tools.values())

        if len(tools) > 0:
            try:
                res = assistant.agent_manager.execute_tools(agent_input=input, tools=tools, assistant=assistant)
                if res is None:
                    input["tool_output"] = ""
                else:
                    tool_output = res["output"]
                    input["tool_output"] = f"## Tool Output: `{tool_output}`" if tool_output else ""

            except Exception as e:
                syslog.error(f"Error when executing tools: {e}")
                traceback.print_exc()

        if "tool_output" not in input:
            input["tool_output"] = ""

        # Embed input
        self.vectorized_input = self._suit.execute_hook("embed_input", input=input["input"], assistant=assistant)

        lt_memory = await assistant.persist_memory.similarity_search(vectorized_input=self.vectorized_input)
        input["persist_memory"] = lt_memory["persist_memory"]

        # fetch document_memory
        try:
            doc = await assistant.document_memory.similarity_search(input["input"])
            document_memory = assistant.agent_manager.execute_documents(
                agent_input={"input": input["input"], "document": doc}, assistant=assistant
            )
            input["document_memory"] = f"## Document Knowledge Output: `{document_memory}`"
        except Exception as e:
            syslog.error(f"Error when fetching document memory: {e}")
            traceback.print_exc()

        if "document_memory" not in input:
            input["document_memory"] = ""

        async for chunk in self._chain.astream(input, assistant.config):
            await handle_chunk(chunk)
