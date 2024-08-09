from typing import Union

from core.utils.decorators import singleton

from ..manager import Manager
from .compiler import Compiler
from .embedder import get_embedder_object
from .llm import get_llm_object
from .memory import DocumentMemory, PersistMemory, ToolKnowledge
from .reranker import get_reranker_object
from .splitter import get_splitter_object


@singleton
class Brain:
    """
    Brain loads the configuration and the modules.
    """

    def __init__(self):
        self.manager = Manager()

        # Load LLM & Embedder
        self.load_natural_language()

        # Load Memories
        self.load_memory()

        # Load Agents
        self.load_agent()

    def load_natural_language(self):
        """
        Load LLM & Embedder
        """
        self.set_llm("LLMChatOpenAI")

        self.set_embedder("EmbedderOpenAI")

        # cfg_cls = get_splitter_by_name("SplitterCharacter")
        # if cfg_cls is None:
        #     raise ValueError("Splitter not found")
        # default_cfg = cfg_cls().model_dump()
        # self.splitter = cfg_cls.get_splitter(default_cfg)
        self.set_splitter("SplitterCharacter")

        self.set_reranker("RerankerCrossEncoder")

    def load_memory(self) -> None:
        """
        Load memories
        """
        self.persist_memory: PersistMemory = PersistMemory()

        self.document_memory: DocumentMemory = DocumentMemory()

        self.tool_knowledge: ToolKnowledge = ToolKnowledge()

    def load_agent(self) -> None:
        """
        Load Agents
        """
        self.compiler = Compiler()

    def set_llm(self, llm_config: Union[str, tuple[str, dict]]) -> None:
        self.llm = get_llm_object(llm_config)

    def set_embedder(self, embedder_config: Union[str, tuple[str, dict]]) -> None:
        self.embedder = get_embedder_object(embedder_config)

    def set_splitter(self, splitter_config: Union[str, tuple[str, dict]]) -> None:
        # Assume that it's being run after change_embedder so that an embedder can be set in case SemanticChunking is used
        self.splitter = get_splitter_object(splitter_config, embedder=self.embedder)

    def set_reranker(self, reranker_config: Union[str, tuple[str, dict]]) -> None:
        self.reranker = get_reranker_object(reranker_config)
