from ...decorators import hook


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

    {chat_history}
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
async def fetch_memory(input, assistant):
    """
    Fetch memory from long term memory

    """
    res = await assistant.long_term_memory.similarity_search(input)
    return res
