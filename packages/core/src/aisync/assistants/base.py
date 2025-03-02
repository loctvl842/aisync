import threading
import time
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Generator, Optional, Union

from aisync.armory import Armory
from aisync.engines.memory import BufferMemory

if TYPE_CHECKING:
    from aisync.suit import Suit


class Assistant(ABC):
    name: str = "Assistant"
    should_exit = threading.Event()

    def __init__(self, suit: str = "mark_i", graph: Optional[str] = None):
        self.buffer_memory: BufferMemory = BufferMemory()
        self.armory: Armory = Armory()
        if suit not in self.armory.suits:
            raise ValueError(f"Suit {suit} not found in armory")
        self._suit = self.armory.activate(suit)

        available_graphs = self._suit.graphs
        if not available_graphs:
            raise ValueError(f"No graphs found in suit {suit}")
        if len(available_graphs) > 1:
            if graph is None:
                print("Available graphs:")
                for idx, graph_name in enumerate(available_graphs.keys(), 1):
                    print(f"{idx}. {graph_name}")

                while True:
                    graph_input = input("Please select a graph by name: ").strip()
                    if graph_input in available_graphs:
                        self.graph = available_graphs[graph_input]
                        break
                    print(f"Invalid graph name. Available graphs: {', '.join(available_graphs.keys())}")

            else:
                if graph not in available_graphs:
                    raise ValueError(
                        f"Graph {graph} not found in suit {suit}. Available graphs: {', '.join(available_graphs.keys())}"
                    )
                self.graph = available_graphs[graph]
        else:
            # Then just choose the only one available
            self.graph = list(self._suit.graphs.values())[0]

        self.graph.compile()

    def start(self, streaming=False) -> None:
        try:
            self.__console_respond(self.greet(streaming=streaming), streaming=streaming)
            while not self.should_exit.is_set():
                print("👨: ", end="", flush=True)
                user_input = input()
                if user_input == "":
                    continue
                if (user_input == "\\exit") or (user_input == "\\quit"):
                    self.should_exit.set()
                else:
                    assistant_response = self.respond(user_input, streaming=streaming)
                    self.__console_respond(assistant_response, streaming=streaming)
        except KeyboardInterrupt:
            self.should_exit.set()
            # Remove tools from vectordb
            print("Exiting gracefully.")

    def __console_respond(self, response: str | Generator[str, None, None], *, streaming: bool = False) -> None:
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

    @property
    def suit(self) -> "Suit":
        return self._suit
