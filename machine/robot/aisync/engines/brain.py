from typing import Union

from core.utils.decorators import singleton

from ..manager import Manager
from .compiler import Compiler
from .embedder import get_embedder_by_name
from .llm import get_llm_by_name
from .memory import DocumentMemory, PersistMemory, ToolKnowledge
from .splitter import get_splitter_by_name


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
        cfg_cls = get_llm_by_name("LLMChatOpenAI")
        if cfg_cls is None:
            raise ValueError("LLM not found")

        default_cfg = cfg_cls().model_dump()
        self.llm = cfg_cls.get_llm(default_cfg)

        cfg_cls = get_embedder_by_name("EmbedderOpenAI")
        if cfg_cls is None:
            raise ValueError("Embedder not found")
        default_cfg = cfg_cls().model_dump()
        self.embedder = cfg_cls.get_embedder(default_cfg)

        cfg_cls = get_splitter_by_name("SplitterCharacter")
        if cfg_cls is None:
            raise ValueError("Splitter not found")
        default_cfg = cfg_cls().model_dump()
        self.splitter = cfg_cls.get_splitter(default_cfg)

    def load_memory(self) -> None:
        """
        Load memories
        """
        self.persist_memory: PersistMemory = PersistMemory()

        self.document_memory: DocumentMemory = DocumentMemory(embedder=self.embedder)

        self.tool_knowledge: ToolKnowledge = ToolKnowledge()

    def load_agent(self) -> None:
        """
        Load Agents
        """
        self.compiler: Compiler = Compiler()

    def get_llm(self, llm_config: Union[str, tuple[str, dict]]):
        if isinstance(llm_config, str):
            cfg_cls = get_llm_by_name(llm_config)
            if cfg_cls is None:
                raise ValueError(f"LLM {llm_config} not found. Using LLMChatOpenAI instead.")

            default_cfg = cfg_cls().model_dump()
            return cfg_cls.get_llm(default_cfg)
        elif isinstance(llm_config, tuple):
            llm_name, llm_schema = llm_config
            if not isinstance(llm_schema, dict) or not isinstance(llm_name, str):
                raise ValueError("Invalid LLM configuration")
            cfg_cls = get_llm_by_name(llm_name)
            if cfg_cls is None:
                raise ValueError(f"LLM {llm_config} not found. Using LLMChatOpenAI instead.")
            return cfg_cls.get_llm(llm_schema)

    def get_embedder(self, embedder_config: Union[str, tuple[str, dict]]):
        if isinstance(embedder_config, str):
            cfg_cls = get_embedder_by_name(embedder_config)
            if cfg_cls is None:
                raise ValueError(f"Embedder {embedder_config} not found. Using EmbedderOpenAI instead.")

            default_cfg = cfg_cls().model_dump()
            return cfg_cls.get_embedder(default_cfg)
        elif isinstance(embedder_config, tuple):
            embedder_name, embedder_schema = embedder_config
            if not isinstance(embedder_schema, dict) or not isinstance(embedder_name, str):
                raise ValueError("Invalid Embedder configuration")
            cfg_cls = get_embedder_by_name(embedder_name)
            if cfg_cls is None:
                raise ValueError(f"Embedder {embedder_name} not found. Using EmbedderOpenAI instead.")
            return cfg_cls.get_embedder(embedder_schema)

    def get_splitter(self, splitter_config: Union[str, tuple[str, dict]]):
        splitter_name, splitter_schema = None, None

        current_splitter = None

        if isinstance(splitter_config, str):
            splitter_name = splitter_config
            cfg_cls = get_splitter_by_name(splitter_config)
            if cfg_cls is None:
                raise ValueError(f"Splitter {splitter_config} not found. Using SplitterCharacter instead.")
            splitter_schema = cfg_cls().model_dump()
        elif isinstance(splitter_config, tuple):
            splitter_name, splitter_schema = splitter_config

        if not isinstance(splitter_schema, dict) or not isinstance(splitter_name, str):
            raise ValueError("Invalid Splitter configuration")
        cfg_cls = get_splitter_by_name(splitter_name)
        if cfg_cls is None:
            raise ValueError(f"Splitter {splitter_name} not found. Using SplitterCharacter instead.")
        current_splitter = cfg_cls.get_splitter(splitter_schema)
        if splitter_name == "SplitterSemantic":
            current_splitter.set_embedder(self.embedder)

        return current_splitter

    def change_llm(self, llm_config: Union[str, tuple[str, dict]]) -> None:
        self.llm = self.get_llm(llm_config)

    def change_embedder(self, embedder_config: Union[str, tuple[str, dict]]) -> None:
        self.embedder = self.get_embedder(embedder_config)

    def change_splitter(self, splitter_config: Union[str, tuple[str, dict]]) -> None:
        # Assume that it's being run after change_embedder so that an embedder can be set in case SemanticChunking is used
        self.splitter = self.get_splitter(splitter_config)
