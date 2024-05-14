from abc import ABC, abstractmethod
from typing import Callable


class Assistant(ABC):
    name: str = "Assistant"
    version: str = "0.1"
    year: int = 2024

    async def start(self, streaming=False):
        try:
            stop = False
            while not stop:
                print("👨: ", end="", flush=True)
                user_input = input()
                if (user_input == "\\exit") or (user_input == "\\quit"):
                    stop = True
                else:
                    if streaming:
                        print("🤖: ", end="", flush=True)
                        await self.streaming(user_input)
                        print("\n")
                    else:
                        assistant_response = self.respond(user_input)
                        print("🤖: ", end="", flush=True)
                        print(assistant_response, "\n")
        except KeyboardInterrupt:
            print("Exiting gracefully.")

    @abstractmethod
    def greet(self) -> str:
        """
        Greet user
        """

    @abstractmethod
    def respond(self, input: str) -> str:
        """
        Respond to user input
        """

    @abstractmethod
    async def streaming(self, input: str, handler: Callable) -> str:
        """
        Stream response to user input
        """
