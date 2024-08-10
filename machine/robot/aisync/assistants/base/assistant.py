from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Callable, Optional

from langchain_core.runnables import RunnableConfig

from ...service import AISyncHandler

if TYPE_CHECKING:
    from ...engines.brain import Brain
    from ...engines.compiler import Compiler
    from ...suit import Suit


class Assistant(ABC):
    name: str = "Assistant"
    version: str = "0.1"
    year: int = 2024
    config: Optional[RunnableConfig] = None

    # Assistant
    brain: "Brain"
    compiler: "Compiler"
    suit: "Suit"

    def __init__(self, config: Optional[RunnableConfig] = None):
        if config is not None:
            # If config is provided, extend it with default callbacks
            config.setdefault("callbacks", []).extend([AISyncHandler()])
            self.config = config
        else:
            # If config is None, initialize it with default callbacks
            self.config = {"callbacks": [AISyncHandler()]}

    async def start(self, streaming=False) -> None:
        try:
            stop = False
            print("🤖: ", end="", flush=True)
            print(self.greet(), "\n")
            while not stop:
                print("👨: ", end="", flush=True)
                user_input = input()
                if (user_input == "\\exit") or (user_input == "\\quit"):
                    await self.turn_off()
                    stop = True
                else:
                    if streaming:
                        # print("🤖: ", end="", flush=True)
                        await self.streaming(user_input)
                        print("\n")
                    else:
                        assistant_response = await self.respond(user_input)
                        print("🤖: ", end="", flush=True)
                        print(assistant_response, "\n")
        except KeyboardInterrupt:
            # Remove tools from vectordb
            await self.turn_off()
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
