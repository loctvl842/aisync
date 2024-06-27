import os

from core.logger import syslog

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
def set_max_token():
    """
    Set the token limit for the assistant

    """
    MY_LIMIT = 1000
    return MY_LIMIT


@hook
def get_path_to_doc():
    """
    Specify your path in to the 'user_path_specify' list as below.

    Example: "home/nhan/aisync/machine/robot/suits/mark_i/document/Rockship.txt"
    """
    user_path_specify = ["~/tet.txt", "~/text.doc", "~/test.txt"]
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
