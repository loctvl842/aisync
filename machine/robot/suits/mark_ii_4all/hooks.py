from ...aisync import hook


@hook
def set_suit_llm(assistant):
    """
    Set the LLM model for the assistant
    Change the model_name to the llm model of your choice.
    """

    model_name = "LLMGPT4All"
    return model_name


@hook
def set_suit_embedder(assistant):
    """
    Set the embedder for the assistant
    Change the model_name to the embedding model of your choice.
    """
    model_name = "EmbedderGPT4All"
    return model_name


@hook
def build_format_instructions(default: str, assistant):
    """
    You can custom your own format instructions here.

    """
    FORMAT_INSTRUCTIONS_GPT4All = """Answer the following question: `{input}`.

    TOOLS:
    ------

    You have access to the following tools:
    {tools}

    Given the question, return the name and input of the tool to use.
    You must ALWAYS return a Python dictionary format with 'name' and 'arguments' keys:

    ```
    {{
        \"name\": \"[tool_name]\",
        \"arguments\":
        {{
            \"tool_arguments\"
        }}
    }}
    ````

    The `arguments` should be a dictionary, with keys corresponding \
    to the argument names and the values corresponding to the requested values.

    Example output:
    ```
    {{
        \"name\": \"get_number\",
        \"arguments\":
        {{

        }}
    }}
    ```

    Begin!
    ## Previous conversation history:

    {buffer_memory}
    Question: {input}
    {agent_scratchpad}"""
    return FORMAT_INSTRUCTIONS_GPT4All


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
def set_document_similarity_search_metric():
    """
    Set the metric for similarity search of document memory
    Should be one of l2_distance, max_inner_product, cosine_distance, l1_distance
    """
    return "l2_distance"

@hook
def set_persist_memory_similarity_search_metric():
    """
    Set the metric for similarity search of persist memory
    Should be one of l2_distance, max_inner_product, cosine_distance, l1_distance
    """
    return "l2_distance"
