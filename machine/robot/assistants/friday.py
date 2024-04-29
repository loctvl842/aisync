from machine.robot.manager import Manager

from .base import Assistant


class Friday(Assistant):
    name = "Friday"
    version = "0.1"
    year = 2024

    def __init__(self):
        self.manager = Manager()

    def greet(self):
        return f"Hello, I am {self.name} {self.version} and I was created in {self.year}"

    def respond(self, input: str) -> str:
        return f"I am {self.name} {self.version} and I was created in {self.year}. You said: {input}"
