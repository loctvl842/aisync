import asyncio
from typing import TYPE_CHECKING, Callable

from core.cache import Cache, DefaultKeyMaker, RedisBackend
from core.logger import syslog

from ..engines.brain import Brain
from ..engines.compiler import AISyncInput
from ..engines.memory import BufferMemory
from ..manager import Manager
from .base import Assistant

if TYPE_CHECKING:
    from ..suit import Suit


class Jarvis(Assistant):
    name = "Jarvis"
    version = "0.1"
    year = 2024

    def __init__(self, suit: str = "mark_i", token_limit=1000):
        super().__init__()
        self.buffer_memory: BufferMemory = BufferMemory()
        self.manager: Manager = Manager()
        self.suit: Suit = self.manager.suits[suit]
        self.customize_llm_and_embedder()
        self.set_max_token(token_limit, suit)
        self.init_cache()

        self.load_document(suit)
        self.turn_on(suit)

        # Compile langgraph workflow
        self.compile()

    def init_cache(self) -> None:
        Cache.configure(backend=RedisBackend(), key_maker=DefaultKeyMaker())

    def set_max_token(self, limit: int, suit: "Suit"):
        if "set_token_limit" in self.manager.suits[suit]._hooks:
            self.max_token = self.manager.suits[suit].execute_hook("set_max_token", default=1000)
        else:
            self.max_token = limit
        if self.max_token <= 0:
            raise ValueError("Token limit must be a positive integer")

    def turn_on(self, suit) -> None:
        self.load_tools(suit)
        self.document_memory.set_similarity_metrics(
            self.suit.execute_hook("set_document_similarity_search_metric", default="l2_distance")
        )
        self.persist_memory.set_similarity_metrics(
            self.suit.execute_hook("set_persist_memory_similarity_search_metric", default="l2_distance")
        )

    async def turn_off(self) -> None:
        # Remove tools from vectordb
        await self.tool_knowledge.remove_tools()

    def customize_llm_and_embedder(self):
        try:
            Brain().change_llm(self.suit.execute_hook("set_suit_llm", assistant=self, default="LLMChatOpenAI"))
        except ValueError as e:
            syslog.error(e)

        try:
            Brain().change_embedder(
                self.suit.execute_hook("set_suit_embedder", assistant=self, default="EmbedderOpenAI")
            )
        except ValueError as e:
            syslog.error(e)

        try:
            Brain().change_splitter(
                self.suit.execute_hook("set_suit_splitter", assistant=self, default="SplitterRecursiveCharacter")
            )
        except ValueError as e:
            syslog.error(e)

        Brain().load_memory()

    def greet(self) -> str:
        return self.suit.execute_hook(
            "set_greeting_message",
            assistant=self,
            default=f"Hello, I am {self.name} {self.version} and I was created in {self.year}",
        )

    def load_document(self, suit):

        file_path = self.suit.execute_hook("get_path_to_doc", default=[])
        """
            If user do not specify the directory
        --> Use default path to doc: ./robot/suits/mark_i
            where 'i' is the suit that the AI wear
        """
        if file_path == []:
            file_path = self.manager.suits[suit]._path_to_doc

        self.all_files_path = file_path

        for fp in file_path:
            self.document_memory.read(suit, fp, self)

    def load_tools(self, suit) -> None:
        tools = list(self.manager.suits[suit].tools.values())
        for tool in tools:
            if hasattr(tool, "set_assistant"):
                tool.set_assistant(self)
        self.tool_knowledge.add_tools(tools=tools, embedder=self.embedder)

    async def save_to_db(self, input: AISyncInput, output: str) -> None:
        vectorized_output = self.suit.execute_hook("embed_output", output=output, assistant=self, default=[0] * 768)
        vectorized_input = self.suit.execute_hook("embed_input", input=input, assistant=self, default=[0] * 768)
        # TODO: Allow user to choose which field(s) to save as input column
        await self.persist_memory.save_interaction(input.query, output, vectorized_input, vectorized_output)

    async def respond(self, input: str) -> str:
        self.buffer_memory.save_pending_message(input)
        customized_input = self.suit.execute_hook(
            "customized_input", query=input, assistant=self, default=AISyncInput(query=input)
        )
        res = await self.compiler.ainvoke(input={"input": customized_input})

        output = res["agent_output"]

        # Save to chat memory
        self.buffer_memory.save_message(sender="Human", message=input)
        self.buffer_memory.save_message(sender="AI", message=output)

        # Save to database
        await self.save_to_db(customized_input, output)

        return output

    async def streaming(
        self,
        input: str,
        handler: Callable = lambda text: print(text, end="", flush=True),
        delay: float = 0.02,
    ):
        self.buffer_memory.save_pending_message(input)

        queue = asyncio.Queue()

        async def proccess_queue(chunk):
            # Follow output format of GPT4All
            chars = list(chunk if isinstance(chunk, str) else chunk.content)
            for c in chars:
                await queue.put(c)

        async def consume_queue(delay: float = 0.01) -> str:
            output = ""
            while True:
                char = await queue.get()
                if char is None:
                    break
                handler(char)
                output += char
                await asyncio.sleep(delay)
            return output

        customized_input = self.suit.execute_hook(
            "customized_input", query=input, assistant=self, default=AISyncInput(query=input)
        )

        producer = asyncio.create_task(
            self.compiler.stream(input={"input": customized_input}, handle_chunk=proccess_queue)
        )
        consumer = asyncio.create_task(consume_queue(delay=delay))
        await producer  # Wait for producer to finish
        await queue.put(None)  # Signal consumer to stop
        output = await consumer  # Wait for consumer to finish

        # Save to chat memory
        self.buffer_memory.save_message(sender="Human", message=input)
        self.buffer_memory.save_message(sender="AI", message=output)

        # Save to database
        await self.save_to_db(customized_input, output)

    @property
    def llm(self):
        return Brain().llm

    @property
    def persist_memory(self):
        return Brain().persist_memory

    @property
    def document_memory(self):
        return Brain().document_memory

    @property
    def embedder(self):
        return Brain().embedder

    @property
    def tool_knowledge(self):
        return Brain().tool_knowledge

    @property
    def compiler(self):
        return Brain().compiler

    @property
    def splitter(self):
        return Brain().splitter

    def compile(self):
        self.compiler.activate(self)
        self.suit.execute_workflow(assistant=self)
        self.compiler.compile()
