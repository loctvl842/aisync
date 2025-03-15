from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from core.assistants.base import Assistant


class BufferMemory(dict):
    def __init__(self, memory_size=100):
        super().__init__({"pending_message": "", "buffer_memory": []})
        self.memory_size = memory_size

    def __call__(self) -> str:
        return self.format_buffer_memory()

    def format_buffer_memory(self, assistant: "Assistant") -> List[tuple]:
        index = len(self["buffer_memory"]) - 1
        buffer_memory: List[tuple] = []
        while index >= 0:
            msg = self["buffer_memory"][index]
            index -= 1
            buffer_memory.append((msg["sender"], msg["message"]))
        buffer_memory.reverse()
        return buffer_memory

    def format_buffer_memory_no_token(self) -> str:
        return "\n".join([f"{msg['sender']}: {msg['message']}" for msg in self["buffer_memory"]])

    def clear_pending_message(self) -> None:
        self["pending_message"] = ""

    def save_message(self, sender: str, message: str) -> None:
        self["buffer_memory"].append({"sender": sender, "message": message})
        self["buffer_memory"] = self["buffer_memory"][-self.memory_size :]

    def save_pending_message(self, message: str) -> None:
        self["pending_message"] = message

    def get_pending_message(self) -> str:
        return self["pending_message"]
