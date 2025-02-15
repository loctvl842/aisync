from abc import ABC, abstractmethod


class BaseBot(ABC):
    """Interface for Chat Bots"""

    is_running = False
    _setup_done = False

    def setup(self):
        """Setup everything needed for the bot

        For example
        - Set up Discord need setup_hook to load cogs
        - Set up Telegram need handlers for commands and normal message
        - Set up console no setup needed
        """
        self._setup_done = True

    @abstractmethod
    def start(self):
        """Start chatting with the bot"""
        if not self._setup_done:
            raise RuntimeError(
                "Bot must be set up before starting. Call setup() first."
            )
        self.is_running = True

    @abstractmethod
    async def astart(self):
        """Start chatting with the bot async"""
        if not self._setup_done:
            raise RuntimeError(
                "Bot must be set up before starting. Call setup() first."
            )
        self.is_running = True

    @abstractmethod
    def stop(self):
        """Stop chatting with the bot"""
        if not self.is_running:
            raise RuntimeError("Bot is not running")
        self.is_running = False

    @abstractmethod
    async def astop(self):
        """Stop chatting with the bot async"""
        if not self.is_running:
            raise RuntimeError("Bot is not running")
        self.is_running = False

    @property
    def running(self) -> bool:
        """Check if the bot is currently running"""
        return self.is_running
