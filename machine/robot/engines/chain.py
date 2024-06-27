import traceback
from typing import Callable, List, Optional

from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnableSequence

from core.logger import syslog

from ..assistants.base.assistant import Assistant
from . import prompts

from tokencost import count_string_tokens


class ChatChain:
    def __init__(self, suit, assistant):
        self._suit = suit
        self._chain = self._make_chain(assistant)

    def _format_input(self, assistant: Assistant):
        return {
            "input": assistant.buffer_memory.get_pending_message(),
            "chat_history": "",
        }

    def _make_prompt(
        self,
        prefix: str = prompts.DEFAULT_PROMPT_PREFIX,
        suffix: str = prompts.DEFAULT_PROMPT_SUFFIX,
        input_variables: Optional[List[str]] = None,
    ):
        template = "\n\n".join([prefix, suffix])
        if input_variables is None:
            input_variables = ["input", "chat_history", "document_memory", "persist_memory", "tool_output"]
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
        self.prompt = self._make_prompt(prefix=prompt_prefix, suffix=prompt_suffix)
        chain = self.prompt | assistant.llm
        return chain
    
    def _add_chat_history(self, input, assistant):
        self.set_buffer_limit(input, assistant)
        return assistant.buffer_memory.format_chat_history(self.buffer_token_limit, self.model_name)
    
    def set_buffer_limit(self, input, assistant):
        print(input)
        filled_prompt = self.prompt.format(**input)
        self.model_name = assistant.llm.model if hasattr(assistant.llm, "model") else assistant.llm.model_name
        syslog.info(self.model_name)

        # Find remaining number of tokens to add to buffer
        self.buffer_token_limit = assistant.max_token - count_string_tokens(filled_prompt, self.model_name)
        syslog.info(f'Max token: {assistant.max_token}, Buffer token limit: {self.buffer_token_limit}')

    async def invoke(self, assistant: Assistant):
        input = self._format_input(assistant)

        # Embed input
        self.vectorized_input = self._suit.execute_hook("embed_input", input=input["input"], assistant=assistant)

        # Run similarity search to find relevant tools
        tools = await assistant.tool_knowledge.find_relevant_tools(
            suit=self._suit, vectorized_input=self.vectorized_input
        )

        if len(tools) > 0:
            try:
                res = assistant.agent_manager.execute_tools(agent_input=input, tools=tools, assistant=assistant)
                if res is None:
                    input["tool_output"] = ""
                else:
                    tool_output = res["output"]
                    input["tool_output"] = f"## Tool Output:\n `{tool_output}`" if tool_output else ""
            except Exception as e:
                syslog.error(f"Error when executing tools: {e}")
                traceback.print_exc()

        if "tool_output" not in input:
            input["tool_output"] = ""

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
        
        # Optimize Chat History
        input["chat_history"] = self._add_chat_history(input, assistant)

        res = {}
        ai_response = self._chain.invoke(input, config=assistant.config)
        if isinstance(ai_response, str):
            res["output"] = ai_response
        else:
            res["output"] = ai_response.content

        return res

    async def stream(self, assistant, handle_chunk: Callable):
        input = self._format_input(assistant)

        # Embed input
        self.vectorized_input = self._suit.execute_hook("embed_input", input=input["input"], assistant=assistant)

        # Run similarity search to find relevant tools
        tools = await assistant.tool_knowledge.find_relevant_tools(
            suit=self._suit, vectorized_input=self.vectorized_input
        )

        if len(tools) > 0:
            try:
                res = assistant.agent_manager.execute_tools(agent_input=input, tools=tools, assistant=assistant)
                if res is None:
                    input["tool_output"] = ""
                else:
                    tool_output = res["output"]
                    input["tool_output"] = f"## Tool Output:\n `{tool_output}`" if tool_output else ""
            except Exception as e:
                syslog.error(f"Error when executing tools: {e}")
                traceback.print_exc()

        if "tool_output" not in input:
            input["tool_output"] = ""

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
        
        # Optimize Chat History
        input["chat_history"] = self._add_chat_history(input, assistant)

        async for chunk in self._chain.astream(input, assistant.config):
            await handle_chunk(chunk)