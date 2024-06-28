from tokencost import count_string_tokens


class BufferMemory(dict):
    def __init__(self, memory_size=100) -> None:
        super().__init__({"pending_message": "", "buffer_memory": []})
        self.memory_size = memory_size

    def __call__(self) -> str:
        return self.format_buffer_memory()

    def format_buffer_memory(self, token_limit, model_name) -> str:
        # Default to show memory_size most recent messages
        if token_limit <= 0:
            return ""

        # Add more messages until token limit is reached
        index = len(self["buffer_memory"]) - 1
        buffer_memory = []
        tot_token = 0
        while index >= 0:
            msg = self["buffer_memory"][index]
            cur_chat_str = f"{msg['sender']}: {msg['message']}"
            cur_chat_token = count_string_tokens(f"{cur_chat_str}\n", model_name)
            tot_token += cur_chat_token
            if tot_token > token_limit:
                break
            index -= 1
            buffer_memory.append(cur_chat_str)
        buffer_memory.reverse()
        return "\n".join(buffer_memory)

    def clear_pending_message(self):
        self["pending_message"] = ""

    def save_message(self, sender: str, message: str):
        self["buffer_memory"].append({"sender": sender, "message": message})
        self["buffer_memory"] = self["buffer_memory"][-self.memory_size :]

    def save_pending_message(self, message: str):
        self["pending_message"] = message

    def get_pending_message(self) -> str:
        return self["pending_message"]
