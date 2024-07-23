import os
from typing import Union

from core.logger import syslog

from ...aisync import AISyncInput, hook


@hook
def set_suit_llm(assistant, default) -> Union[str, tuple[str, dict]]:
    """
    Set the LLM model for the assistant
    Change the model_name to the llm model of your choice.
    """

    model_name = "LLMChatOllama"
    model_config = {"model": "llama3-chatqa"}
    return model_name, model_config


@hook
def set_suit_embedder(assistant, default) -> Union[str, tuple[str, dict]]:
    """
    Set the embedder for the assistant
    Change the model_name to the embedding model of your choice.
    """
    model_name = "EmbedderLocal"
    model_config = {"model_name_or_path": "BAAI/bge-base-en-v1.5"}
    return model_name, model_config


@hook
def set_suit_splitter(assistant, default) -> Union[str, tuple[str, dict]]:
    """
    Set the splitter for processing documents
    Should be one of [SplitterRecursiveCharacter, SplitterCharacter, SplitterSemantic]
    """
    model_name = "SplitterRecursiveCharacter"
    return model_name


@hook
def build_format_instructions(default: str, assistant):
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
def customized_input(query: str, assistant, default):
    """
    You can customize the input here

    """
    EMAIL_MARKDOWN_HELP = """
    Please use markdown format for the email content. Use **bold** or *italic* or both for highlight
    important content like names, service... ensure that each section are seperated
    by double newlines, and most IMPORTANTLY with the sign section, the complimentary closings part, name part, and position part
    must be separated by a double space like this "  ". Example:

    Best regards,
    Fravist SG

    Your message STRICTLY follow the rules below:
    - Language: English
    - Tone: formal, friendly, and witty
    - Word limit: 50 to 120 words
    - Do not make up any information that is not provided in the context.
    - No subject line is needed.
    """

    class MyInput(AISyncInput):
        name: str
        EMAIL_MARKDOWN_HELP: str

    return MyInput(query=query, name="Nhan", EMAIL_MARKDOWN_HELP=EMAIL_MARKDOWN_HELP)


@hook
def set_max_token(default):
    """
    Set the token limit for the assistant

    """
    MY_LIMIT = 1000
    return MY_LIMIT


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
