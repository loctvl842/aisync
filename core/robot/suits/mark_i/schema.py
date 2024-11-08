from typing import Annotated, TypedDict


def add_messages(messages: list[tuple[str, str]], new_messages: list[tuple[str, str]]) -> list[tuple[str, str]]:
    """Function to add a new message to the messages list."""
    return messages + new_messages


class State(TypedDict):
    messages: Annotated[list[tuple[str, str]], add_messages]
