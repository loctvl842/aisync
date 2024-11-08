from typing import TYPE_CHECKING, Dict, Generator, Literal, Union

from langchain_core.prompts import ChatPromptTemplate

from .prompts import DEFAULT_SYSTEM_PROMPT
from ..schemas import Message

if TYPE_CHECKING:
    from langchain_core.runnables import Runnable

    from ..assistants.base import Assistant
    from ..decorators.hook import SupportedHook
    from ..suit import Suit


class Chain:
    def __init__(self, suit: "Suit", assistant: "Assistant"):
        self._assistant = assistant
        self._suit = suit

    @property
    def suit(self) -> "Suit":
        return self._suit

    @property
    def assistant(self) -> "Assistant":
        return self._assistant

    @property
    def supported_hook(self) -> "SupportedHook":
        from ..decorators import SupportedHook

        return SupportedHook

    def construct_prompt(self) -> list[tuple[Literal["system", "human", "ai"], str]]:
        system_message = self.suit.execute_hook(self.supported_hook.SYSTEM_PROMPT, default=DEFAULT_SYSTEM_PROMPT)
        messages: list[tuple[Literal["system", "human", "ai"], str]] = [
            ("system", system_message),
            ("human", "{input}"),
        ]
        return messages

    def invoke(self, input: str, *, streaming: bool = False) -> Union[Message, Generator[Message, None, None]]:
        prompt = ChatPromptTemplate.from_messages(self.construct_prompt())
        chain: "Runnable" = prompt | self.assistant.llm
        if streaming:
            return chain.stream({"input": input})
        else:
            response = chain.invoke({"input": input})
            return Message(content=response.content)

    def _stream(self, chain: "Runnable", input: Dict) -> Generator[Message, None, None]:
        for chunk in chain.stream(input):
            yield Message(content=chunk.content)

    async def ainvoke(self, input: str, *, streaming: bool = False):
        return f"You said: {input}"
