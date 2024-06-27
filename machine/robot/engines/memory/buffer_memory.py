from tokencost import count_string_tokens


class BufferMemory(dict):
    def __init__(self, memory_size=100) -> None:
        super().__init__({"pending_message": "", "chat_history": []})
        self.memory_size = memory_size

    def __call__(self) -> str:
        return self.format_chat_history()

    def format_chat_history(self, token_limit, model_name) -> str:
        # Default to show memory_size most recent messages
        if token_limit <= 0:
            return ""

        # Add more messages until token limit is reached
        index = len(self["chat_history"]) - 1
        chat_history = []
        tot_token = 0
        while index >= 0:
            msg = self["chat_history"][index]
            cur_chat_str = f"{msg['sender']}: {msg['message']}"
            cur_chat_token = count_string_tokens(f"{cur_chat_str}\n", model_name)
            tot_token += cur_chat_token
            if tot_token > token_limit:
                break
            index -= 1
            chat_history.append(cur_chat_str)
        chat_history.reverse()
        return "\n".join(chat_history)

    def clear_pending_message(self):
        self["pending_message"] = ""

    def save_message(self, sender: str, message: str):
        self["chat_history"].append({"sender": sender, "message": message})
        self["chat_history"] = self["chat_history"][-self.memory_size :]

    def save_pending_message(self, message: str):
        self["pending_message"] = message

    def get_pending_message(self) -> str:
        return self["pending_message"]
