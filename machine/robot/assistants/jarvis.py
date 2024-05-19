import asyncio
from typing import Callable

from machine.robot.engines.brain import Brain
from machine.robot.engines.chain import ChatChain
from machine.robot.engines.memory import BufferMemory
from machine.robot.manager import Manager

from .base import Assistant


class Jarvis(Assistant):
    name = "Jarvis"
    version = "0.1"
    year = 2024

    def __init__(self, suit="mark_i"):
        super().__init__()
        self.buffer_memory = BufferMemory()
        self.manager = Manager()
        self._chain = ChatChain(self.manager.suits[suit], self)

    def greet(self):
        return f"Hello, I am {self.name} {self.version} and I was created in {self.year}"

    def respond(self, input: str) -> str:
        self.buffer_memory.save_pending_message(input)
        res = self._chain.execute(self)
        output = res["output"]

        # Save to chat memory
        self.buffer_memory.save_message(sender="Human", message=input)
        self.buffer_memory.save_message(sender="AI", message=output)

        return output

    async def _consume_queue(self, queue: asyncio.Queue, handler: Callable, delay: float = 0.01) -> str:
        output = ""
        while True:
            char = await queue.get()
            if char is None:
                break
            handler(char)
            output += char
            await asyncio.sleep(delay)
        return output

    async def streaming(
        self,
        input: str,
        handler: Callable = lambda word: print(word, end="", flush=True),
        delay: float = 0.01,
    ):
        self.buffer_memory.save_pending_message(input)

        queue = asyncio.Queue()
        producer = asyncio.create_task(self._chain.process_stream(self, queue))
        consumer = asyncio.create_task(self._consume_queue(queue, handler, delay))
        await producer  # Wait for producer to finish
        await queue.put(None)  # Signal consumer to stop
        output = await consumer  # Wait for consumer to finish

        # Save to chat memory
        self.buffer_memory.save_message(sender="Human", message=input)
        self.buffer_memory.save_message(sender="AI", message=output)

    @property
    def chain(self):
        return self._chain

    @property
    def llm(self):
        return Brain().llm
