from core.utils.decorators import singleton
from machine.robot.manager import Manager

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

    def load_natural_language(self):
        """
        Load LLM & Embedder
        """
        cfg_cls = get_llm_by_name("LLMChatGoogleGenerativeAI")
        if cfg_cls is None:
            raise ValueError("LLM not found")

        default_cfg = cfg_cls().model_dump()
        self.llm = cfg_cls.get_llm(default_cfg)
