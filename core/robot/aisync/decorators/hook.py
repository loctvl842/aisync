import enum


class Hook:
    def __init__(self, call_fn):
        self.call = call_fn
        self.name = call_fn.__name__

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} {self.name}>"


class SupportedHook(str, enum.Enum):
    BEFORE_READ_MESSAGE = "before_read_message"
    BEFORE_SEND_MESSAGE = "before_send_message"
    SYSTEM_PROMPT = "build_system_prompt"
    SUIT_LLM = "set_suit_llm"


def hook(*args, **kwargs):
    def decorator(fn):
        return Hook(fn)

    if len(args) == 1 and len(kwargs) == 0 and callable(args[0]):
        # called as @hook
        return Hook(args[0])
    else:
        # called as @hook(*args, **kwargs)
        return decorator
