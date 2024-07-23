from ...aisync import hook


@hook
def build_prompt_prefix(default: str, assistant):
    """
    You can custom your own prompt prefix here.

    `prompt_prefix` mission is to define what is the role of Chatbot.
    """
    CUSTOMIZED_PROMPT = """
    You are a smart customer service assistant for Kravist, a gym and martial art center.
    Customer will ask you about Kravist via email, and you will use the provided information to answer the user.
    Step 1: Check if the user's question is clear. If not, ask the user to rephrase their question.
    Step 2: Check if the user's question is related to the related to the company,
    respond that the question is not relevant and ask the user to ask a question related to Kravist.
    Step 3: Check if the provided document contains information to answer the customer's question.
    If there is no related information, or the information is not clear, you will just need to response with `[CANNOT ANSWER]` at the beginning, then follow up with the reason why you cannot or not confidence to reply them.
    Expected output if you have information: An email with markdown format:

    {EMAIL_MARKDOWN_HELP}

    Use your memory to get the following details to generate the email:
    Customer info: {name}
    """
    return CUSTOMIZED_PROMPT


@hook
def build_prompt_suffix(default: str, assistant):
    """
    You can custom your own prompt suffix here.

    `prompt_suffix` mission is to define the structure of a conversation.
    """
    return default


@hook
def build_prompt_from_docs(assistant, default):
    """
    You can custom your own long-term memory prompt here.

    `long_term_prompt` mission is to define the structure of a long-term memory.
    """
    DOC_PROMPT = """
    Answer the following query: `{input}`.
    Ignore all document knowledge that are not relevant to the query.
    Use the following document knowledge to answer the query to the best of your ability:

    {document}
    """
    return DOC_PROMPT
