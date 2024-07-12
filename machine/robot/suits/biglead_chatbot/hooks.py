import os

from core.logger import syslog

from ...decorators import hook


@hook
def set_suit_llm(assistant):
    """
    Set the LLM model for the assistant
    Change the model_name to the llm model of your choice.
    """

    model_name = "LLMChatOllama"
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
def set_greeting_message(assistant):
    """
    You can custom your own greeting message here.

    """
    message = """Xin chào! Tôi là trợ lý thông minh của công ty BigLead. Tôi có thể cung cấp thông tin về công ty và trả lời câu hỏi của bạn về BigLead. Hãy hỏi tôi về thông tin bạn muốn biết về công ty nhé!
        """

    return message


@hook
def get_path_to_doc():
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
