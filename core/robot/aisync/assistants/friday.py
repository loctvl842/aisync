import time
from typing import Generator, Union

from .base import Assistant


class Friday(Assistant):
    name = "Friday"

    def __init__(self, suit: str = "mark_i"):
        super().__init__()

    def greet(self, *, streaming: bool = False) -> str:
        response = f"Hello, I am {self.__class__.__name__}. How can I help you today?"
        if not streaming:
            return response
        else:
            return self._streaming(response)

    async def agreet(self, *, streaming: bool = False) -> str:
        return self.greet()

    def respond(self, input: str, *, streaming: bool = False) -> Union[str, Generator[str, None, None]]:
        response = f"You said: {input}"
        if not streaming:
            return response
        else:
            return self._streaming(response)

    async def arespond(self, input: str, *, streaming: bool = False) -> Union[str, Generator[str, None, None]]:
        return self.respond(input)

    def _streaming(self, response: str) -> Generator[str, None, None]:
        for char in response:
            time.sleep(0.02)
            yield char
