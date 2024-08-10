from typing import TYPE_CHECKING, Optional, Union

from core.utils.decorators import singleton

from ..decorators.hook import HookOptions
from .embedder import get_embedder_object
from .llm import get_llm_object
from .memory import DocumentMemory, PersistMemory, ToolKnowledge
from .reranker import get_reranker_object
from .splitter import get_splitter_object

if TYPE_CHECKING:
    from ..assistants.base import Assistant


@singleton
class Brain:
    """
    Brain loads the configuration and the modules.
    """

    def __init__(self, assistant: Optional["Assistant"] = None):
        # Load LLM & Embedder
        self.load_natural_language(assistant)

        # Load Memories
        self.load_memory()

    def load_natural_language(self, assistant: Optional["Assistant"] = None) -> None:
        """
        Load LLM & Embedder
        """

        def load(hook_option: HookOptions, default: str) -> Union[str, tuple[str, dict]]:
            return assistant.suit.execute_hook(hook_option, assistant=assistant, default=default) if assistant else default

        self.set_llm(load(HookOptions.SET_SUIT_LLM, default="LLMChatOpenAI"))
        self.set_embedder(load(HookOptions.SET_SUIT_EMBEDDER, default="EmbedderOpenAI"))
        self.set_splitter(load(HookOptions.SET_SUIT_SPLITTER, default="SplitterRecursiveCharacter"))
        self.set_reranker(load(HookOptions.SET_SUIT_RERANKER, default="RerankerCrossEncoder"))

    def load_memory(self) -> None:
        """
        Load memories
        """
        self.persist_memory: PersistMemory = PersistMemory()

        self.document_memory: DocumentMemory = DocumentMemory()

        self.tool_knowledge: ToolKnowledge = ToolKnowledge()

    def set_llm(self, llm_cls_name: Union[str, tuple[str, dict]]) -> None:
        self.llm = get_llm_object(llm_cls_name)

    def set_embedder(self, embedder_cls_name: Union[str, tuple[str, dict]]) -> None:
        self.embedder = get_embedder_object(embedder_cls_name)

    def set_splitter(self, splitter_cls_name: Union[str, tuple[str, dict]]) -> None:
        # Assume that it's being run after change_embedder so that an embedder can be set in case SemanticChunking is used
        self.splitter = get_splitter_object(splitter_cls_name, embedder=self.embedder)

    def set_reranker(self, reranker_cls_name: Union[str, tuple[str, dict]]) -> None:
        self.reranker = get_reranker_object(reranker_cls_name)
