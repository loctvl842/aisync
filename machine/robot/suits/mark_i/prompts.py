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


@hook
def build_prompt_from_docs(assistant):
    """
    You can custom your own long-term memory prompt here.

    `long_term_prompt` mission is to define the structure of a long-term memory.
    """
    LONG_TERM_PROMPT = """
    Answer the following question: `{input}`.
<<<<<<< HEAD
    Ignore all document knowledge that are not relevant to the question.
=======
>>>>>>> b928a3dce4a7081a2d985aa1397f1d4d9a4b98fc
    Use the following document knowledge to answer the question to the best of your ability:

    {document}
    """
    return LONG_TERM_PROMPT
