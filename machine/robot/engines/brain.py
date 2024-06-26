from core.utils.decorators import singleton
from machine.robot.engines.memory import DocumentMemory, PersistMemory

from ..manager import Manager
from .agent_manager import AgentManager
from .embedder import get_embedder_by_name
from .llm import get_llm_by_name


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

    def load_memory(self):
        """
        Load memories
        """
        self.persist_memory = PersistMemory()

        self.document_memory = DocumentMemory(embedder=self.embedder)

    def load_agent(self):
        """
        Load Agents
        """
        self.agent_manager = AgentManager()
