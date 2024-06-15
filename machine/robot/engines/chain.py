import traceback
import json

from typing import Callable, List, Optional

from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnableSequence
from sqlalchemy import create_engine, text, select
from sqlalchemy.orm import sessionmaker 
from ..assistants.base.assistant import Assistant
from . import prompts
from numpy.linalg import norm as l2_distance


from core.logger import syslog
from machine.models import ChatInput, ChatOutput

class ChatChain:
    def __init__(self, suit, assistant, top_matches: Optional[int] = 10):
        self._suit = suit
        self._chain = self._make_chain(assistant)
        self._top_matches = top_matches

        # TODO: Move engine out of chain
        self._engine = create_engine("postgresql://postgres:12345@localhost:5432/aisync")
        self._Session = sessionmaker(bind=self._engine)
        ChatInput.__table__.create(self._engine, checkfirst=True)
        ChatOutput.__table__.create(self._engine, checkfirst=True)

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

    def invoke(self, assistant: Assistant):
        input = self._format_input(assistant)

        #Get tools from all chatbot suits
        tools = list(self._suit.tools.values())

        if len(tools) > 0:
            try: 
                res = assistant.agent_manager.execute_tools(agent_input=input, tools=tools, assistant=assistant)
                tool_output = res["output"]
                input["tool_output"] = f"## Tool Output: `{tool_output}`" if tool_output else ""
            except Exception as e:
                syslog.error(f"Error when executing tools: {e}")
                traceback.print_exc()

        if "tool_output" not in input:
            input["tool_output"] = ""
        
        # Embed input
        self.vectorized_input = self._suit.execute_hook("embed_input", input=input["input"], assistant=assistant)

        # DB Session for similarity search
        with self._Session() as session:
            session.execute(text('CREATE EXTENSION IF NOT EXISTS vector'))

            # Top self._top_matches similarity search neighbors from input and output tables
            input_match = session.scalars(select(ChatInput).order_by(ChatInput.embedding.l2_distance(self.vectorized_input)).limit(self._top_matches))
            output_match = session.scalars(select(ChatOutput).order_by(ChatOutput.embedding.l2_distance(self.vectorized_input)).limit(self._top_matches))
            
            # Top self._top_matches closest neighbors combined
            result = list(input_match) + list(output_match)
            # Result sorted by l2 distance
            res_by_l2 = sorted(result, key=lambda x: l2_distance(x.embedding - self.vectorized_input))[:self._top_matches]
            
            input["long_term_memory"] = "## Past interaction:\n\n"
            for res in res_by_l2:
                payload = json.loads(res.payload)
                input["long_term_memory"] += f'Human: {payload["input"]}\nAI: {payload["output"]}\n\n'
            session.commit()

        if "long_term_memory" not in input:
            input["long_term_memory"] = ""

        res = {}
        ai_response = self._chain.invoke(input, assistant.config)
        res["output"] = ai_response.content

        return res

    async def stream(self, assistant, handle_chunk: Callable):
        input = self._format_input(assistant)

        #Get tools from all chatbot suits
        tools = list(self._suit.tools.values())

        if len(tools) > 0:
            try: 
                res = assistant.agent_manager.execute_tools(agent_input=input, tools=tools, assistant=assistant)
                tool_output = res["output"]
                input["tool_output"] = f"## Tool Output: `{tool_output}`" if tool_output else ""
            except Exception as e:
                syslog.error(f"Error when executing tools: {e}")
                traceback.print_exc()

        if "tool_output" not in input:
            input["tool_output"] = ""

        # Embed input
        self.vectorized_input = self._suit.execute_hook("embed_input", input=input["input"], assistant=assistant)

        # DB Session for similarity search
        with self._Session() as session:
            session.execute(text('CREATE EXTENSION IF NOT EXISTS vector'))

            # Top self._top_matches similarity search neighbors from input and output tables
            input_match = session.scalars(select(ChatInput).order_by(ChatInput.embedding.l2_distance(self.vectorized_input)).limit(self._top_matches))
            output_match = session.scalars(select(ChatOutput).order_by(ChatOutput.embedding.l2_distance(self.vectorized_input)).limit(self._top_matches))
            
            # Top self._top_matches closest neighbors combined
            result = list(input_match) + list(output_match)
            # Result sorted by l2 distance
            res_by_l2 = sorted(result, key=lambda x: l2_distance(x.embedding - self.vectorized_input))[:self._top_matches]
            
            input["long_term_memory"] = "## Past interaction:\n\n"
            for res in res_by_l2:
                payload = json.loads(res.payload)
                input["long_term_memory"] += f'Human: {payload["input"]}\nAI: {payload["output"]}\n\n'
            session.commit()

        if "long_term_memory" not in input:
            input["long_term_memory"] = ""

        async for chunk in self._chain.astream(input, assistant.config):
            await handle_chunk(chunk)
