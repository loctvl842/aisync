from ...decorators import hook


@hook
def set_suit_llm(assistant):
    """
    Set the LLM model for the assistant
    Change the model_name to the llm model of your choice.
    """

    model_name = "LLMChatOpenAI"
    return model_name


@hook
def set_suit_embedder(assistant):
    """
    Set the embedder for the assistant
    Change the model_name to the embedding model of your choice.
    """
    model_name = "EmbedderOpenAI"
    return model_name


@hook
def build_format_instructions(default: str, assistant):
    """
    You can custom your own format instructions here.

    """
    return default


@hook
def embed_input(input: str, assistant):
    """
    You can embed user's input here for similarity search

    """
    return assistant.embedder.embed_query(text=input)


@hook
def embed_output(output: str, assistant):
    """
    You can embed assistant's output here for similarity search

    """
    return assistant.embedder.embed_query(text=output)


@hook
async def fetch_memory(input, assistant):
    """
    Fetch memory from long term memory

    """
    res = await assistant.long_term_memory.similarity_search(input)
    return res
