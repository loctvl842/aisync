from core.utils.decorators import singleton
from machine.robot.manager import Manager
from machine.robot.engines.llm import get_llm


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
        self.llm = get_llm("LLMChatOpenAI")
