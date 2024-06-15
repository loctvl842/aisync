import asyncio
import json
from typing import Callable

from ..engines.brain import Brain
from ..engines.chain import ChatChain
from ..engines.memory import BufferMemory
from ..manager import Manager
from .base import Assistant
from machine.models import ChatInput, ChatOutput


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
    
    def save_to_db(self, input: str, output: str):
        vectorized_output = self._chain._suit.execute_hook("embed_output", output=output, assistant=self)
        with self._chain._Session() as session:
            payload = {
                "input": input,
                "output": output,
            }
            session.add(ChatOutput(payload=json.dumps(payload), embedding=vectorized_output))
            session.add(ChatInput(payload=json.dumps(payload), embedding=self._chain.vectorized_input))
            session.commit()

    def respond(self, input: str) -> str:
        self.buffer_memory.save_pending_message(input)
        res = self._chain.invoke(self)
        output = res["output"]

        # Save to chat memory
        self.buffer_memory.save_message(sender="Human", message=input)
        self.buffer_memory.save_message(sender="AI", message=output)

        # Save to database
        self.save_to_db(input, output)

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
            chars = list(chunk.content)
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

        producer = asyncio.create_task(self._chain.stream(self, handle_chunk=proccess_queue))
        consumer = asyncio.create_task(consume_queue(delay=delay))
        await producer  # Wait for producer to finish
        await queue.put(None)  # Signal consumer to stop
        output = await consumer  # Wait for consumer to finish

        # Save to chat memory
        self.buffer_memory.save_message(sender="Human", message=input)
        self.buffer_memory.save_message(sender="AI", message=output)

        # Save to database
        self.save_to_db(input, output)

    @property
    def chain(self):
        return self._chain

    @property
    def llm(self):
        return Brain().llm
    
    @property
    def agent_manager(self):
        return Brain().agent_manager
    
    @property
    def embedder(self):
        return Brain().embedder
