import os

from core.logger import syslog

from ...aisync import AISyncInput, hook


@hook
def set_suit_llm(assistant, default):
    """
    Set the LLM model for the assistant
    Change the model_name to the llm model of your choice.
    """

    model_name = "LLMChatOpenAI"
    return model_name


@hook
def set_suit_embedder(assistant, default):
    """
    Set the embedder for the assistant
    Change the model_name to the embedding model of your choice.
    """
    model_name = "EmbedderOpenAI"
    return model_name


@hook
def build_prompt_tool_calling(default: str, assistant):
    """
    You can custom your own format instructions here.

    """
    return default


@hook
def embed_input(input: AISyncInput, assistant, default):
    """
    You can embed user's input here for similarity search

    """
    return assistant.embedder.embed_query(text=input.query)


@hook
def embed_output(output: str, assistant, default):
    """
    You can embed assistant's output here for similarity search

    """
    return assistant.embedder.embed_query(text=output)


@hook
def set_greeting_message(assistant, default):
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


@hook
def get_path_to_doc(default):
    """
    Specify your path in to the 'user_path_specify' list as below.

    Example: "home/nhan/aisync/machine/robot/suits/mark_i/document/Rockship.txt"
    """
    user_path_specify = []
    filter_path = []
    for i in range(len(user_path_specify)):
        try:
            # Get the absolute directory path to document
            corrected_file_path = os.path.expanduser(user_path_specify[i])

            # Raise error if the path did not exist
            if not os.path.exists(corrected_file_path):
                raise FileNotFoundError(f"File does not exist: {corrected_file_path}")

            filter_path.append(f"{corrected_file_path}")
        except FileNotFoundError as e:
            syslog.error(str(e))
        except Exception as e:
            syslog.error(f"An unexpected error occurred: {str(e)}")
    return filter_path


@hook
def set_document_similarity_search_metric(default):
    """
    Set the metric for similarity search of document memory
    Should be one of l2_distance, max_inner_product, cosine_distance, l1_distance
    """
    return "l2_distance"


@hook
def set_persist_memory_similarity_search_metric(default):
    """
    Set the metric for similarity search of persist memory
    Should be one of l2_distance, max_inner_product, cosine_distance, l1_distance
    """
    return "l2_distance"


@hook
def customized_input(query: str, assistant, default):
    """
    You can customize the input here

    """

    return AISyncInput(query=query)
