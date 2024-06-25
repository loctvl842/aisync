from ...decorators import hook


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

# TODO
@hook
async def fetch_memory(input, assistant):
    """
    Fetch memory from long term memory

    """
    res = await assistant.long_term_memory.similarity_search(input)
    return res


@hook
async def fetch_document_memory(input, assistant):
    """
    Fetch document memory

    """

    doc = await assistant.document_memory.similarity_search(input)
    return assistant.agent_manager.execute_documents(agent_input={"input": input, "document": doc}, assistant=assistant)
