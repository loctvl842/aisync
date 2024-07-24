from ...aisync import hook


@hook
def build_prompt_prefix(default: str, assistant):
    """
    You can custom your own prompt prefix here.

    `prompt_prefix` mission is to define what is the role of Chatbot.
    """
    CUSTOMIZED_PROMPT = """
    <|begin_of_text|><|start_header_id|>system<|end_header_id|>
    You are a smart customer service assistant for Kravist, a gym and martial art center.
    Customer will ask you about Kravist via email, and you will use the provided information to answer the user. 
    Step 1: Check if the user's question is clear. If not, ask the user to rephrase their question. 
    Step 2: Check if the user's question is related to the related to the company,
    respond that the question is not relevant and ask the user to ask a question related to Kravist.
    Step 3: Check if the provided document contains information to answer the customer's question.

    Expected output if you have information: An email with markdown format:

    {EMAIL_MARKDOWN_HELP}

    Expected output if you do not have enough information: `[CANNOT ANSWER]` followed by the reason why you cannot answer the question.

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
    CUSTOMIZED_SUFFIX = """
    # Context:

    ## Buffer Memory:

    {buffer_memory}

    {document_memory}

    <|eot_id|><|start_header_id|>user<|end_header_id|>{query}
    <|start_header_id|>assistant<|end_header_id|>:"""
    return CUSTOMIZED_SUFFIX


@hook
def build_prompt_from_docs(assistant, default):
    """
    You can custom your own long-term memory prompt here.

    `long_term_prompt` mission is to define the structure of a long-term memory.
    """
    DOC_PROMPT = """
    <|begin_of_text|><|start_header_id|>system<|end_header_id|>
    Ignore all document knowledge that are not relevant to the query.
    Use the following document knowledge to answer the query to the best of your ability:

    {document}

    # Answer the following query: `{query}`.
    """
    return DOC_PROMPT
