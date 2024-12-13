from typing import TYPE_CHECKING, Generator, Union

from aisync.armory import Armory
from aisync.assistants.base import Assistant
from aisync.decorators.hook import SupportedHook
from aisync.engines.graph import TChunk
from aisync.engines.memory import BufferMemory

if TYPE_CHECKING:
    from aisync.suit import Suit


class Jarvis(Assistant):
    name = "Jarvis"

    def __init__(self, suit: str = "mark_i"):
        super().__init__()
        self.buffer_memory: BufferMemory = BufferMemory()
        self.armory: Armory = Armory()
        if suit not in self.armory.suits:
            raise ValueError(f"Suit {suit} not found in armory")
        suit_ = self.armory.suits[suit]
        self._suit = suit_
        self.workflow = list(suit_.graphs.values())[0]
        self.workflow.compile()

    def greet(self, *, streaming: bool = False) -> str:
        response = f"Hello, I am {self.__class__.__name__}. How can I help you today?"
        return response

    async def agreet(self, *, streaming: bool = False) -> str:
        return self.greet()

    def respond(self, input: str, *, streaming: bool = False) -> Union[TChunk, Generator[TChunk, None, None]]:
        self.buffer_memory.save_pending_message(input)

        def on_chain_start(input):
            return self.suit.execute_hook(SupportedHook.BEFORE_READ_MESSAGE, input, default=input)

        def on_chunk_generated(chunk):
            return self.suit.execute_hook(SupportedHook.BEFORE_SEND_MESSAGE, chunk, default=chunk)

        if not streaming:
            return self.workflow.invoke(
                input,
                on_chain_start=on_chain_start,
                on_chunk_generated=on_chunk_generated,
            )
        return self.workflow.stream(
            input,
            stream_mode=["updates", "messages"],
            on_chain_start=on_chain_start,
            on_chunk_generated=on_chunk_generated,
        )

    async def arespond(self, input: str, *, streaming: bool = False) -> Union[str, Generator[str, None, None]]:
        return self.respond(input)

    @property
    def suit(self) -> "Suit":
        return self._suit
