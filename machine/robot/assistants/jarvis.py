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

    @property
    def chain(self):
        return self._chain

    @property
    def llm(self):
        return Brain().llm
