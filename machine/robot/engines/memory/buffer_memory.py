class BufferMemory(dict):
    def __init__(self, memory_size=10) -> None:
        super().__init__({"pending_message": "", "chat_history": []})
        self.memory_size = memory_size

    def __call__(self) -> str:
        return self.format_chat_history()

    def format_chat_history(self):
        return "\n".join([f"{msg['sender']}: {msg['message']}" for msg in self["chat_history"]])

    def clear_pending_message(self):
        self["pending_message"] = ""

    def save_message(self, sender: str, message: str):
        self["chat_history"].append({"sender": sender, "message": message})
        self["chat_history"] = self["chat_history"][-self.memory_size :]

    def save_pending_message(self, message: str):
        self["pending_message"] = message

    def get_pending_message(self) -> str:
        return self["pending_message"]
