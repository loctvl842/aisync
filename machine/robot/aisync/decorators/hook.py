from enum import Enum


class SuitHook:
    def __init__(self, call_fn):
        self.call = call_fn
        self.name = call_fn.__name__

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} {self.name}>"


class HookOptions(Enum):
    BUILD_FORMAT_INSTRUCTIONS = "build_format_instructions"
    BUILD_PROMPT_FROM_DOCS = "build_prompt_from_docs"
    BUILD_PROMPT_PREFIX = "build_prompt_prefix"
    BUILD_PROMPT_SUFFIX = "build_prompt_suffix"
    CUSTOMIZED_INPUT = "customized_input"
    EMBED_INPUT = "embed_input"
    EMBED_OUTPUT = "embed_output"
    GET_PATH_TO_DOC = "get_path_to_doc"
    SET_DOCUMENT_SIMILARITY_SEARCH_METRIC = "set_document_similarity_search_metric"
    SET_GREETING_MESSAGE = "set_greeting_message"
    SET_MAX_TOKEN = "set_max_token"
    SET_PERSIST_MEMORY_SIMILARITY_SEARCH_METRIC = "set_persist_memory_similarity_search_metric"
    SET_SUIT_EMBEDDER = "set_suit_embedder"
    SET_SUIT_LLM = "set_suit_llm"
    SET_SUIT_SPLITTER = "set_suit_splitter"
    SHOULD_CUSTOMIZE_NODE_LLM = "should_customize_node_llm"


def hook(*args, **kwargs):
    def decorator(fn):
        return SuitHook(fn)

    if len(args) == 1 and len(kwargs) == 0 and callable(args[0]):
        # called as @hook
        return SuitHook(args[0])
    else:
        # called as @hook(*args, **kwargs)
        return decorator
