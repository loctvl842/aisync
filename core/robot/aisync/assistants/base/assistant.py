import time
from abc import ABC, abstractmethod
from typing import Generator, Union


class Assistant(ABC):
    name: str = "Assistant"

    def __init__(self):
        pass

    def start(self, streaming=False) -> None:
        try:
            stop = False
            self.__console_respond(self.greet(streaming=streaming), streaming=streaming)
            while not stop:
                print("👨: ", end="", flush=True)
                user_input = input()
                if user_input == "":
                    continue
                if (user_input == "\\exit") or (user_input == "\\quit"):
                    stop = True
                else:
                    assistant_response = self.respond(user_input, streaming=streaming)
                    self.__console_respond(assistant_response, streaming=streaming)
        except KeyboardInterrupt:
            # Remove tools from vectordb
            print("Exiting gracefully.")

    def __console_respond(self, response: str, *, streaming: bool = False) -> None:
        print("🤖: ", end="", flush=True)
        if not streaming:
            print(response, "\n")
        else:
            for chunk in response:
                for char in chunk:
                    print(char, end="", flush=True)
                    time.sleep(0.01)
            print("\n")

    @abstractmethod
    def greet(self, *, streaming: bool = False) -> Union[str, Generator[str, None, None]]:
        """
        Greet user
        """

    @abstractmethod
    async def agreet(self, *, streaming: bool = False) -> Union[str, Generator[str, None, None]]:
        return self.greet()

    @abstractmethod
    def respond(self, input: str, *, streaming: bool = False) -> Union[str, Generator[str, None, None]]:
        """
        Respond to user input
        """

    @abstractmethod
    async def arespond(self, input: str, *, streaming: bool = False) -> Union[str, Generator[str, None, None]]:
        return self.respond(input, streaming=streaming)
