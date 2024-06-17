from abc import ABC, abstractmethod
from typing import Callable, Optional

from langchain_core.runnables import RunnableConfig
from langfuse.callback import CallbackHandler


class Assistant(ABC):
    name: str = "Assistant"
    version: str = "0.1"
    year: int = 2024
    config: Optional[RunnableConfig] = None

    def __init__(self, config: Optional[RunnableConfig] = None):
        if config is not None:
            # If config is provided, extend it with default callbacks
            config.setdefault("callbacks", []).extend([CallbackHandler()])
            self.config = config
        else:
            # If config is None, initialize it with default callbacks
            self.config = {"callbacks": [CallbackHandler()]}

    async def start(self, streaming=False):
        try:
            stop = False
            print("🤖: ", end="", flush=True)
            print(self.greet(), "\n")
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
                        assistant_response = await self.respond(user_input)
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
