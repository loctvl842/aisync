from abc import ABC, abstractmethod


class Assistant(ABC):
    name: str = "Assistant"
    version: str = "0.1"
    year: int = 2024

    def start(self):
        try:
            stop = False
            while not stop:
                user_input = input("👨: ")
                if (user_input == "\\exit") or (user_input == "\\quit"):
                    stop = True
                else:
                    assistant_response = self.respond(user_input)
                    print(f"\n🤖 ({self.name}): ", assistant_response, "\n")
        except KeyboardInterrupt:
            print("Exiting gracefully.")

    @abstractmethod
    def greet(self) -> str:
        """
        Greet user
        """

    @abstractmethod
    def respond(self, input) -> str:
        """
        Respond to user input
        """
