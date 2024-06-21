from ...decorators import hook


@hook
def build_prompt_prefix(default: str, assistant):
    """
    You can custom your own prompt prefix here.

    `prompt_prefix` mission is to define what is the role of Chatbot.
    """
    return default


@hook
def build_prompt_suffix(default: str, assistant):
    """
    You can custom your own prompt suffix here.

    `prompt_suffix` mission is to define the structure of a conversation.
    """
    return default
