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


@hook
def set_greeting_message(assistant):
    """
    You can custom your own greeting message here.

    """
    message = (
        "Good day! "
        "I am a consultant representing Rockship,"
        " dedicated to simplifying your journey by providing tailored solutions. "
        "My expertise lies in understanding your unique needs and guiding you towards the most suitable options. "
        "Please feel free to share your requirements, and I will try my best to assist you."
    )

    return message
